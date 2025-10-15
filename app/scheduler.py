#!/usr/bin/env python3
"""
结构化智能电梯调度算法
支持多种调度算法：SCAN, LOOK, 最短路径, 负载均衡, 自适应等
"""
from typing import List, Dict, Optional, Set
from collections import deque
from abc import ABC, abstractmethod

from elevator_saga.client.base_controller import ElevatorController
from elevator_saga.client.proxy_models import (
    ProxyElevator, ProxyFloor, ProxyPassenger
)
from elevator_saga.core.models import Direction, SimulationEvent


class SchedulingAlgorithm(ABC):
    """调度算法抽象基类"""
    
    def __init__(self, max_floor: int):
        self.max_floor = max_floor
    
    @abstractmethod
    def initialize_elevator(self, elevator: ProxyElevator, elevator_id: int) -> None:
        """初始化电梯"""
        pass
    
    @abstractmethod
    def handle_idle_elevator(self, elevator: ProxyElevator, targets: deque) -> None:
        """处理空闲电梯"""
        pass
    
    @abstractmethod
    def calculate_cost(self, elevator: ProxyElevator, target_floor: int, direction: Direction) -> float:
        """计算电梯到达目标楼层的成本"""
        pass


class SCANAlgorithm(SchedulingAlgorithm):
    """SCAN算法实现"""
    
    def initialize_elevator(self, elevator: ProxyElevator, elevator_id: int) -> None:
        target_floor = (elevator_id * (self.max_floor - 1)) // 2
        elevator.go_to_floor(target_floor, immediate=True)
        # 注意：target_floor_direction 是只读属性，不能直接设置
    
    def handle_idle_elevator(self, elevator: ProxyElevator, targets: deque) -> None:
        if not targets:
            # 没有目标，开始扫描
            if elevator.current_floor == 0:
                elevator.go_to_floor(self.max_floor)
            elif elevator.current_floor == self.max_floor:
                elevator.go_to_floor(0)
            else:
                # 继续当前方向
                if elevator.target_floor_direction == Direction.UP:
                    elevator.go_to_floor(self.max_floor)
                else:
                    elevator.go_to_floor(0)
        else:
            next_target = targets[0]
            elevator.go_to_floor(next_target)
    
    def calculate_cost(self, elevator: ProxyElevator, target_floor: int, direction: Direction) -> float:
        distance_cost = abs(elevator.current_floor - target_floor)
        
        # 方向成本
        if elevator.target_floor_direction != Direction.STOPPED and elevator.target_floor_direction != direction:
            direction_cost = 10
        else:
            direction_cost = 0
        
        # 负载成本
        load_cost = len(elevator.passengers) * 2
        
        return distance_cost + direction_cost + load_cost


class LOOKAlgorithm(SchedulingAlgorithm):
    """LOOK算法实现"""
    
    def initialize_elevator(self, elevator: ProxyElevator, elevator_id: int) -> None:
        target_floor = (elevator_id * (self.max_floor - 1)) // 2
        elevator.go_to_floor(target_floor, immediate=True)
        # 注意：target_floor_direction 是只读属性
    
    def handle_idle_elevator(self, elevator: ProxyElevator, targets: deque) -> None:
        if not targets:
            # LOOK算法：只在有请求时才改变方向
            if elevator.target_floor_direction == Direction.UP:
                elevator.go_to_floor(self.max_floor)
            else:
                elevator.go_to_floor(0)
        else:
            next_target = targets[0]
            elevator.go_to_floor(next_target)
    
    def calculate_cost(self, elevator: ProxyElevator, target_floor: int, direction: Direction) -> float:
        distance_cost = abs(elevator.current_floor - target_floor)
        
        # LOOK算法更注重方向匹配
        if elevator.target_floor_direction != Direction.STOPPED and elevator.target_floor_direction != direction:
            direction_cost = 15  # 更高的方向惩罚
        else:
            direction_cost = 0
        
        load_cost = len(elevator.passengers) * 2
        
        return distance_cost + direction_cost + load_cost


class ShortestPathAlgorithm(SchedulingAlgorithm):
    """最短路径算法实现"""
    
    def initialize_elevator(self, elevator: ProxyElevator, elevator_id: int) -> None:
        # 初始位置在中间楼层
        target_floor = self.max_floor // 2
        elevator.go_to_floor(target_floor, immediate=True)
        # 注意：target_floor_direction 是只读属性
    
    def handle_idle_elevator(self, elevator: ProxyElevator, targets: deque) -> None:
        if targets:
            # 选择最近的未处理目标
            next_target = min(targets, key=lambda t: abs(elevator.current_floor - t))
            elevator.go_to_floor(next_target)
        else:
            # 没有目标时保持在当前位置
            pass
    
    def calculate_cost(self, elevator: ProxyElevator, target_floor: int, direction: Direction) -> float:
        # 最短路径算法主要考虑距离
        distance_cost = abs(elevator.current_floor - target_floor)
        load_cost = len(elevator.passengers) * 3  # 更高的负载惩罚
        
        return distance_cost + load_cost


class LoadBalancingAlgorithm(SchedulingAlgorithm):
    """负载均衡算法实现"""
    
    def initialize_elevator(self, elevator: ProxyElevator, elevator_id: int) -> None:
        # 分散初始位置
        target_floor = (elevator_id * self.max_floor) // 2
        elevator.go_to_floor(target_floor, immediate=True)
        # 注意：target_floor_direction 是只读属性
    
    def handle_idle_elevator(self, elevator: ProxyElevator, targets: deque) -> None:
        if targets:
            next_target = targets[0]
            elevator.go_to_floor(next_target)
        else:
            # 负载均衡：寻找负载较轻的区域
            if len(elevator.passengers) < 4:  # 如果负载较轻
                elevator.go_to_floor(self.max_floor // 2)  # 移动到中心位置
    
    def calculate_cost(self, elevator: ProxyElevator, target_floor: int, direction: Direction) -> float:
        distance_cost = abs(elevator.current_floor - target_floor)
        
        # 负载均衡：优先选择负载较轻的电梯
        load_factor = len(elevator.passengers) / 8.0  # 假设最大容量为8
        load_cost = load_factor * 20  # 负载惩罚
        
        return distance_cost + load_cost


class AdaptiveAlgorithm(SchedulingAlgorithm):
    """自适应算法实现"""
    
    def __init__(self, max_floor: int):
        super().__init__(max_floor)
        self.request_history: Dict[int, List[int]] = {}  # 楼层请求历史
    
    def initialize_elevator(self, elevator: ProxyElevator, elevator_id: int) -> None:
        target_floor = self.max_floor // 2
        elevator.go_to_floor(target_floor, immediate=True)
        # 注意：target_floor_direction 是只读属性
    
    def handle_idle_elevator(self, elevator: ProxyElevator, targets: deque) -> None:
        if targets:
            # 自适应：根据历史数据选择目标
            next_target = self._select_adaptive_target(elevator, targets)
            elevator.go_to_floor(next_target)
        else:
            # 移动到最常请求的楼层
            if self.request_history:
                most_requested = max(self.request_history.keys(), 
                                   key=lambda f: len(self.request_history[f]))
                elevator.go_to_floor(most_requested)
    
    def _select_adaptive_target(self, elevator: ProxyElevator, targets: deque) -> int:
        """根据历史数据选择最佳目标"""
        if not targets:
            return elevator.current_floor
        
        # 优先选择历史请求较多的楼层
        scored_targets = []
        for target in targets:
            score = len(self.request_history.get(target, []))
            scored_targets.append((target, score))
        
        # 按分数排序，选择分数最高的
        scored_targets.sort(key=lambda x: x[1], reverse=True)
        return scored_targets[0][0]
    
    def calculate_cost(self, elevator: ProxyElevator, target_floor: int, direction: Direction) -> float:
        distance_cost = abs(elevator.current_floor - target_floor)
        
        # 自适应：考虑历史请求频率
        history_factor = len(self.request_history.get(target_floor, [])) * 0.5
        load_cost = len(elevator.passengers) * 2
        
        return distance_cost - history_factor + load_cost  # 历史请求多的楼层成本更低


class SmartElevatorController(ElevatorController):
    """
    智能电梯调度控制器
    基于原始框架，支持多种调度算法
    """
    
    def __init__(self, algorithm: str = "scan", debug: bool = False):
        super().__init__()
        self.debug = debug
        self.algorithm_name = algorithm
        
        # 算法实例
        self.algorithm: SchedulingAlgorithm = self._create_algorithm(algorithm)
        
        # 电梯状态管理
        self.elevator_targets: Dict[int, deque] = {}
        self.elevator_directions: Dict[int, Direction] = {}
        self.elevator_destinations: Dict[int, deque] = {}
        
        # 乘客管理
        self.all_passengers: List[ProxyPassenger] = []
        self.pending_requests: Dict[Direction, Set[int]] = {
            Direction.UP: set(),
            Direction.DOWN: set()
        }
    
    def _create_algorithm(self, algorithm_name: str) -> SchedulingAlgorithm:
        """创建算法实例"""
        max_floor = 5  # 假设最大楼层为5
        
        if algorithm_name == "scan":
            return SCANAlgorithm(max_floor)
        elif algorithm_name == "look":
            return LOOKAlgorithm(max_floor)
        elif algorithm_name == "shortest":
            return ShortestPathAlgorithm(max_floor)
        elif algorithm_name == "load_balance":
            return LoadBalancingAlgorithm(max_floor)
        elif algorithm_name == "adaptive":
            return AdaptiveAlgorithm(max_floor)
        else:
            # 默认使用SCAN算法
            return SCANAlgorithm(max_floor)
    
    def on_init(self, elevators: List[ProxyElevator], floors: List[ProxyFloor]) -> None:
        """初始化回调"""
        if self.debug:
            print(f"🚀 初始化 {self.algorithm_name.upper()} 算法控制器")
            print(f"📊 电梯数量: {len(elevators)}, 楼层数量: {len(floors)}")
        
        self.elevators = elevators
        self.floors = floors
        
        # 初始化电梯状态
        for i, elevator in enumerate(elevators):
            self.elevator_targets[elevator.id] = deque()
            self.elevator_directions[elevator.id] = Direction.STOPPED
            self.elevator_destinations[elevator.id] = deque()
            
            # 使用算法初始化电梯
            self.algorithm.initialize_elevator(elevator, i)
            
            if self.debug:
                print(f"  🛗 电梯 E{elevator.id} 初始化完成")
    
    def on_passenger_call(self, passenger: ProxyPassenger, floor: ProxyFloor, direction: str) -> None:
        """乘客呼叫回调"""
        if self.debug:
            print(f"📞 乘客 {passenger.id} F{floor.floor} 请求 {passenger.origin} -> {passenger.destination} ({direction})")
        
        self.all_passengers.append(passenger)
        
        # 分配乘客到最佳电梯
        assigned_elevator = self._assign_passenger_to_elevator(passenger, floor, Direction(direction))
        if assigned_elevator:
            if self.debug:
                print(f"  → 分配给电梯 E{assigned_elevator.id}")
            
            # 添加乘客的出发楼层到电梯目标队列
            if passenger.origin not in self.elevator_targets[assigned_elevator.id]:
                self.elevator_targets[assigned_elevator.id].append(passenger.origin)
                self._update_elevator_targets(assigned_elevator)
        else:
            # 如果没有合适的电梯，添加到待处理请求
            self.pending_requests[Direction(direction)].add(passenger.origin)
            if self.debug:
                print(f"  → 添加到待处理请求")
    
    def _assign_passenger_to_elevator(
        self, passenger: ProxyPassenger, floor: ProxyFloor, direction: Direction
    ) -> Optional[ProxyElevator]:
        """根据算法逻辑分配乘客到最佳电梯"""
        best_elevator: Optional[ProxyElevator] = None
        min_cost = float('inf')
        
        for elevator in self.elevators:
            # 使用算法计算成本
            cost = self.algorithm.calculate_cost(elevator, passenger.origin, direction)
            
            # 检查电梯是否能够接载乘客
            if self._can_elevator_pickup(elevator, floor.floor, direction):
                if cost < min_cost:
                    min_cost = cost
                    best_elevator = elevator
        
        return best_elevator
    
    def _can_elevator_pickup(self, elevator: ProxyElevator, floor: int, direction: Direction) -> bool:
        """检查电梯是否能够接载乘客"""
        # 检查容量
        if len(elevator.passengers) >= 8:  # 假设最大容量为8
            return False
        
        # 检查方向
        if elevator.target_floor_direction == Direction.STOPPED:
            return True
        
        if elevator.target_floor_direction == direction:
            if direction == Direction.UP and elevator.current_floor <= floor:
                return True
            elif direction == Direction.DOWN and elevator.current_floor >= floor:
                return True
        
        return False
    
    def _update_elevator_targets(self, elevator: ProxyElevator) -> None:
        """更新电梯目标队列"""
        if not self.elevator_targets[elevator.id]:
            return
        
        # 根据算法处理目标队列
        self.algorithm.handle_idle_elevator(elevator, self.elevator_targets[elevator.id])
    
    def on_elevator_idle(self, elevator: ProxyElevator) -> None:
        """电梯空闲回调"""
        if self.debug:
            print(f"🛗 电梯 E{elevator.id} 空闲")
        
        # 处理待处理请求
        self._process_pending_requests(elevator)
        
        # 更新电梯目标
        self._update_elevator_targets(elevator)
    
    def _process_pending_requests(self, elevator: ProxyElevator) -> None:
        """处理待处理请求"""
        for direction in [Direction.UP, Direction.DOWN]:
            if self.pending_requests[direction]:
                # 找到最近的待处理请求
                nearest_request = min(
                    self.pending_requests[direction],
                    key=lambda floor: abs(elevator.current_floor - floor)
                )
                
                # 检查是否可以接载
                if self._can_elevator_pickup(elevator, nearest_request, direction):
                    self.elevator_targets[elevator.id].append(nearest_request)
                    self.pending_requests[direction].remove(nearest_request)
                    self._update_elevator_targets(elevator)
                    break
    
    def on_elevator_stopped(self, elevator: ProxyElevator, floor: ProxyFloor) -> None:
        """电梯停靠回调"""
        if self.debug:
            print(f"🛑 电梯 E{elevator.id} 停靠在 F{floor.floor}")
        
        # 移除已到达的目标
        if floor.floor in self.elevator_targets[elevator.id]:
            self.elevator_targets[elevator.id].remove(floor.floor)
        
        # 更新电梯方向
        if self.elevator_targets[elevator.id]:
            next_target = self.elevator_targets[elevator.id][0]
            if next_target > elevator.current_floor:
                self.elevator_directions[elevator.id] = Direction.UP
            elif next_target < elevator.current_floor:
                self.elevator_directions[elevator.id] = Direction.DOWN
            else:
                self.elevator_directions[elevator.id] = Direction.STOPPED
        else:
            self.elevator_directions[elevator.id] = Direction.STOPPED
    
    def on_passenger_board(self, elevator: ProxyElevator, passenger: ProxyPassenger) -> None:
        """乘客上梯回调"""
        if self.debug:
            print(f"⬆️ 乘客{passenger.id} 上电梯 E{elevator.id} F{elevator.current_floor} -> F{passenger.destination}")
        
        # 添加乘客目的地到电梯目标队列
        if passenger.destination not in self.elevator_targets[elevator.id]:
            self.elevator_targets[elevator.id].append(passenger.destination)
            if self.debug:
                print(f"  → 添加目标 F{passenger.destination} 到电梯 E{elevator.id}")
    
    def on_passenger_alight(self, elevator: ProxyElevator, passenger: ProxyPassenger, floor: ProxyFloor) -> None:
        """乘客下梯回调"""
        if self.debug:
            print(f"⬇️ 乘客{passenger.id} 下电梯 E{elevator.id} F{floor.floor}")
        
        # 移除已到达的目的地
        if passenger.destination in self.elevator_targets[elevator.id]:
            self.elevator_targets[elevator.id].remove(passenger.destination)
    
    def on_elevator_passing_floor(self, elevator: ProxyElevator, floor: ProxyFloor, direction: str) -> None:
        """电梯经过楼层回调"""
        if self.debug:
            print(f"🚶 电梯 E{elevator.id} 经过 F{floor.floor} ({direction})")
    
    def on_elevator_approaching(self, elevator: ProxyElevator, floor: ProxyFloor, direction: str) -> None:
        """电梯接近楼层回调"""
        if self.debug:
            print(f"🔔 电梯 E{elevator.id} 接近 F{floor.floor} ({direction})")
    
    def on_event_execute_start(
        self, tick: int, events: List[SimulationEvent], 
        elevators: List[ProxyElevator], floors: List[ProxyFloor]
    ) -> None:
        """事件执行开始回调"""
        if self.debug and events:
            print(f"Tick {tick}: 处理 {len(events)} 个事件")
            for event in events:
                if event.type.value == "elevator_move":
                    elevator = next((e for e in elevators if e.id == event.data["elevator"]), None)
                    if elevator:
                        direction_symbol = elevator.target_floor_direction.value[0] if elevator.target_floor_direction else '●'
                        print(f"🛗 电梯{elevator.id} 状态:{elevator.run_status} 方向:{direction_symbol} 位置:{elevator.current_floor:.1f} 目标:{elevator.target_floor}")
    
    def on_event_execute_end(
        self, tick: int, events: List[SimulationEvent], 
        elevators: List[ProxyElevator], floors: List[ProxyFloor]
    ) -> None:
        """事件执行结束回调"""
        pass


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 运行单个算法
        algorithm_name = sys.argv[1]
        print(f"测试算法: {algorithm_name}")
        controller = SmartElevatorController(algorithm=algorithm_name, debug=True)
        try:
            controller.start()
        except KeyboardInterrupt:
            print(f"\n{algorithm_name} 算法被用户中断")
        finally:
            controller.stop()
    else:
        # 测试不同算法
        algorithms = ["scan", "look", "shortest", "load_balance", "adaptive"]
        for algo in algorithms:
            print(f"\n测试算法: {algo}")
            controller = SmartElevatorController(algorithm=algo, debug=True)
            try:
                controller.start()
            except KeyboardInterrupt:
                print(f"\n{algo} 算法被用户中断")
            finally:
                controller.stop()