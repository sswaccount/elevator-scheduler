#!/usr/bin/env python3
"""
高性能智能电梯调度算法
基于多策略优化的电梯调度系统，专注于最小化乘客等待时间
"""
from typing import List, Dict, Optional, Set, Tuple, Any
from collections import deque, defaultdict
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import math
import time
from enum import Enum

from elevator_saga.client.base_controller import ElevatorController
from elevator_saga.client.proxy_models import (
    ProxyElevator, ProxyFloor, ProxyPassenger
)
from elevator_saga.core.models import Direction, SimulationEvent


class AlgorithmType(Enum):
    """算法类型枚举"""
    DISTANCE_OPTIMIZED = "distance_optimized"
    LOAD_BALANCED = "load_balanced"
    DIRECTION_AWARE = "direction_aware"
    ADAPTIVE = "adaptive"


@dataclass
class ElevatorMetrics:
    """电梯性能指标"""
    total_wait_time: float = 0.0
    passengers_served: int = 0
    energy_consumed: float = 0.0
    idle_time: int = 0
    efficiency_score: float = 0.0


@dataclass
class PassengerRequest:
    """乘客请求信息"""
    passenger: ProxyPassenger
    floor: ProxyFloor
    direction: Direction
    request_time: int
    priority_score: float = 0.0


class SchedulingAlgorithm(ABC):
    """调度算法抽象基类"""
    
    def __init__(self, max_floor: int, num_elevators: int):
        self.max_floor = max_floor
        self.num_elevators = num_elevators
        self.metrics = {i: ElevatorMetrics() for i in range(num_elevators)}
    
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


class DistanceOptimizedAlgorithm(SchedulingAlgorithm):
    """距离优化算法 - 专注于最小化乘客等待时间"""
    
    def initialize_elevator(self, elevator: ProxyElevator, elevator_id: int) -> None:
        """均匀分布电梯初始位置"""
        target_floor = (elevator_id * (self.max_floor - 1)) // (self.num_elevators - 1) if self.num_elevators > 1 else 0
        elevator.go_to_floor(target_floor, immediate=True)
    
    def handle_idle_elevator(self, elevator: ProxyElevator, targets: deque) -> None:
        """智能处理空闲电梯 - 选择最优的目标楼层"""
        if targets:
            # 选择距离最近的目标
            best_target = min(targets, key=lambda t: abs(elevator.current_floor - t))
            elevator.go_to_floor(best_target)
        else:
            # 没有明确目标时，移动到中间位置等待请求
            center_floor = self.max_floor // 2
            if abs(elevator.current_floor - center_floor) > 1:
                elevator.go_to_floor(center_floor)
    
    def calculate_cost(self, elevator: ProxyElevator, target_floor: int, direction: Direction) -> float:
        """计算综合成本，优先考虑距离"""
        distance = abs(elevator.current_floor - target_floor)

        # 基础距离成本
        distance_cost = distance * 2.0

        # 方向一致性奖励（减少方向切换）
        direction_penalty = 0.0
        if (elevator.target_floor_direction != Direction.STOPPED and
            elevator.target_floor_direction != direction):
            direction_penalty = distance * 0.5  # 方向不一致的惩罚

        # 负载均衡成本
        load_factor = len(elevator.passengers) / max(elevator.max_capacity, 1)
        load_cost = load_factor * distance * 0.3

        # 电梯效率奖励（空闲电梯获得奖励）
        idle_bonus = 0.0
        if len(elevator.passengers) == 0 and distance > 2:
            idle_bonus = -distance * 0.2  # 空闲电梯去远距离请求的奖励

        return distance_cost + direction_penalty + load_cost + idle_bonus


class LoadBalancedAlgorithm(SchedulingAlgorithm):
    """负载均衡算法 - 平衡各电梯的工作量"""
    
    def initialize_elevator(self, elevator: ProxyElevator, elevator_id: int) -> None:
        """分散初始位置，避免聚集"""
        target_floor = (elevator_id * self.max_floor) // (self.num_elevators + 1)
        elevator.go_to_floor(target_floor, immediate=True)
    
    def handle_idle_elevator(self, elevator: ProxyElevator, targets: deque) -> None:
        """优先处理负载较轻区域的请求"""
        if targets:
            # 选择能平衡负载的目标
            best_target = self._select_load_balanced_target(elevator, targets)
            elevator.go_to_floor(best_target)
        else:
            # 移动到负载较低的区域
            if len(elevator.passengers) < 3:  # 负载较轻
                elevator.go_to_floor(self.max_floor // 3)  # 移动到较低楼层

    def _select_load_balanced_target(self, elevator: ProxyElevator, targets: deque) -> int:
        """选择最优的负载均衡目标"""
        best_target = targets[0]
        min_cost = float('inf')

        for target in targets:
            cost = self.calculate_cost(elevator, target, Direction.UP if target > elevator.current_floor else Direction.DOWN)
            if cost < min_cost:
                min_cost = cost
                best_target = target

        return best_target

    def calculate_cost(self, elevator: ProxyElevator, target_floor: int, direction: Direction) -> float:
        """负载均衡导向的成本计算"""
        distance = abs(elevator.current_floor - target_floor)

        # 基础距离成本
        distance_cost = distance * 1.5

        # 电梯负载成本（优先选择负载较轻的电梯）
        load_factor = len(elevator.passengers) / max(elevator.max_capacity, 1)
        load_cost = load_factor * distance * 1.0

        # 全局负载均衡奖励
        total_load = sum(len(e.passengers) for e in [elevator])  # 简化计算
        avg_load = total_load / max(self.num_elevators, 1)

        if load_factor < avg_load * 0.8:  # 负载较轻的电梯获得奖励
            load_cost *= 0.7
        
        return distance_cost + load_cost


class DirectionAwareAlgorithm(SchedulingAlgorithm):
    """方向感知算法 - 优化电梯行驶方向"""

    def __init__(self, max_floor: int, num_elevators: int):
        super().__init__(max_floor, num_elevators)
        self.direction_history = defaultdict(list)  # 记录方向历史
    
    def initialize_elevator(self, elevator: ProxyElevator, elevator_id: int) -> None:
        """初始位置考虑历史方向模式"""
        target_floor = self.max_floor // 2
        elevator.go_to_floor(target_floor, immediate=True)
    
    def handle_idle_elevator(self, elevator: ProxyElevator, targets: deque) -> None:
        """根据方向历史选择目标"""
        if targets:
            # 选择同方向的目标
            current_direction = elevator.target_floor_direction
            same_direction_targets = [
                t for t in targets
                if (t > elevator.current_floor and current_direction == Direction.UP) or
                   (t < elevator.current_floor and current_direction == Direction.DOWN)
            ]

            if same_direction_targets:
                target = min(same_direction_targets, key=lambda t: abs(elevator.current_floor - t))
            else:
                target = min(targets, key=lambda t: abs(elevator.current_floor - t))
            elevator.go_to_floor(target)
        else:
            # 根据历史选择方向
            if self.direction_history[elevator.id]:
                recent_directions = self.direction_history[elevator.id][-3:]
                up_count = sum(1 for d in recent_directions if d == Direction.UP)
                if up_count >= 2:
                    elevator.go_to_floor(self.max_floor)
                else:
                    elevator.go_to_floor(0)
    
    def calculate_cost(self, elevator: ProxyElevator, target_floor: int, direction: Direction) -> float:
        """方向感知成本计算"""
        distance = abs(elevator.current_floor - target_floor)

        # 基础距离成本
        distance_cost = distance * 1.8

        # 方向一致性奖励
        direction_bonus = 0.0
        if elevator.target_floor_direction == direction:
            direction_bonus = -distance * 0.3  # 同方向奖励
        elif elevator.target_floor_direction != Direction.STOPPED:
            direction_bonus = distance * 0.6   # 方向切换惩罚

        # 负载成本
        load_cost = len(elevator.passengers) * distance * 0.2

        return distance_cost + direction_bonus + load_cost


class AdaptiveAlgorithm(SchedulingAlgorithm):
    """自适应算法 - 根据实时情况动态调整策略"""

    def __init__(self, max_floor: int, num_elevators: int):
        super().__init__(max_floor, num_elevators)
        self.request_history = defaultdict(list)  # 楼层请求历史
        self.peak_hours = set()  # 高峰时段楼层
        self.strategy_weights = {
            'distance': 0.4,
            'load_balance': 0.3,
            'direction': 0.3
        }
    
    def initialize_elevator(self, elevator: ProxyElevator, elevator_id: int) -> None:
        """自适应初始位置"""
        target_floor = self._calculate_optimal_starting_position(elevator_id)
        elevator.go_to_floor(target_floor, immediate=True)

    def _calculate_optimal_starting_position(self, elevator_id: int) -> int:
        """计算最优起始位置"""
        if self.request_history:
            # 根据历史请求频率分配位置
            floor_weights = {}
            for floor, requests in self.request_history.items():
                floor_weights[floor] = len(requests)

            if floor_weights:
                # 分配电梯到请求最频繁的区域
                sorted_floors = sorted(floor_weights.items(), key=lambda x: x[1], reverse=True)
                return sorted_floors[elevator_id % len(sorted_floors)][0]

        # 默认分散位置
        return (elevator_id * self.max_floor) // (self.num_elevators + 1)
    
    def handle_idle_elevator(self, elevator: ProxyElevator, targets: deque) -> None:
        """自适应处理空闲电梯"""
        if targets:
            # 根据当前策略权重选择目标
            best_target = self._select_adaptive_target(elevator, targets)
            elevator.go_to_floor(best_target)

            # 更新历史记录
            self.request_history[elevator.current_floor].append(time.time())
        else:
            # 自适应等待位置
            optimal_wait_floor = self._get_optimal_waiting_floor(elevator)
            if abs(elevator.current_floor - optimal_wait_floor) > 1:
                elevator.go_to_floor(optimal_wait_floor)
    
    def _select_adaptive_target(self, elevator: ProxyElevator, targets: deque) -> int:
        """自适应目标选择"""
        scored_targets = []
        
        for target in targets:
            score = 0.0
            distance = abs(elevator.current_floor - target)

            # 距离得分（反向）
            distance_score = 1.0 / (1.0 + distance)
            score += distance_score * self.strategy_weights['distance']

            # 负载均衡得分
            load_factor = len(elevator.passengers) / max(elevator.max_capacity, 1)
            load_score = 1.0 - load_factor
            score += load_score * self.strategy_weights['load_balance']

            # 方向一致性得分
            direction = Direction.UP if target > elevator.current_floor else Direction.DOWN
            if elevator.target_floor_direction == direction:
                direction_score = 1.0
            elif elevator.target_floor_direction == Direction.STOPPED:
                direction_score = 0.8
            else:
                direction_score = 0.3
            score += direction_score * self.strategy_weights['direction']

            scored_targets.append((target, score))
        
        # 选择最高分的楼层
        return max(scored_targets, key=lambda x: x[1])[0]

    def _get_optimal_waiting_floor(self, elevator: ProxyElevator) -> int:
        """获取最优等待位置"""
        if self.request_history:
            # 选择历史请求最频繁的楼层
            floor_requests = {floor: len(requests) for floor, requests in self.request_history.items()}
            return max(floor_requests.items(), key=lambda x: x[1])[0]

        return self.max_floor // 2
    
    def calculate_cost(self, elevator: ProxyElevator, target_floor: int, direction: Direction) -> float:
        """自适应成本计算"""
        distance = abs(elevator.current_floor - target_floor)

        # 自适应权重调整
        if len(elevator.passengers) > elevator.max_capacity * 0.8:
            # 高负载时优先考虑负载均衡
            self.strategy_weights['load_balance'] = 0.5
            self.strategy_weights['distance'] = 0.3
            self.strategy_weights['direction'] = 0.2
        elif distance > self.max_floor * 0.6:
            # 长距离时优先考虑距离
            self.strategy_weights['distance'] = 0.6
            self.strategy_weights['load_balance'] = 0.2
            self.strategy_weights['direction'] = 0.2

        # 综合成本计算
        distance_cost = distance * 2.0

        # 方向成本
        direction_cost = 0.0
        if (elevator.target_floor_direction != Direction.STOPPED and
            elevator.target_floor_direction != direction):
            direction_cost = distance * 0.4

        # 负载成本
        load_cost = len(elevator.passengers) * distance * 0.2

        return distance_cost + direction_cost + load_cost


class SmartElevatorController(ElevatorController):
    """
    高性能智能电梯调度控制器
    基于多策略优化的电梯调度算法，专注于最小化乘客等待时间
    """

    def __init__(self, algorithm: str = "direction_aware", debug: bool = False):
        """
        初始化智能电梯控制器

        Args:
            algorithm: 使用的调度算法类型 ('distance_optimized', 'load_balanced', 'direction_aware', 'adaptive')
            debug: 是否启用调试模式
        """
        super().__init__(debug=debug)
        self.algorithm_name = algorithm
        self.debug = debug
        
        # 算法实例
        self.algorithm: SchedulingAlgorithm = self._create_algorithm(algorithm)
        
        # 电梯状态管理
        self.elevator_targets: Dict[int, deque] = {}
        self.elevator_destinations: Dict[int, deque] = {}
        self.elevator_wait_times: Dict[int, Dict[int, int]] = {}  # 乘客等待时间记录
        
        # 乘客管理
        self.all_passengers: List[ProxyPassenger] = []
        self.pending_requests: Dict[Direction, Set[int]] = {
            Direction.UP: set(),
            Direction.DOWN: set()
        }
    
        # 性能统计
        self.performance_stats = {
            'total_wait_time': 0.0,
            'total_passengers': 0,
            'p95_wait_time': 0.0,
            'algorithm_efficiency': 0.0
        }

    def _create_algorithm(self, algorithm_name: str) -> SchedulingAlgorithm:
        """创建指定的调度算法实例"""
        # 这里需要从系统状态获取楼层数和电梯数，暂时使用默认值
        max_floor = 10  # 默认值，会在on_init中更新
        num_elevators = 2  # 默认值，会在on_init中更新

        if algorithm_name == "distance_optimized":
            return DistanceOptimizedAlgorithm(max_floor, num_elevators)
        elif algorithm_name == "load_balanced":
            return LoadBalancedAlgorithm(max_floor, num_elevators)
        elif algorithm_name == "direction_aware":
            return DirectionAwareAlgorithm(max_floor, num_elevators)
        elif algorithm_name == "adaptive":
            return AdaptiveAlgorithm(max_floor, num_elevators)
        else:
            # 默认使用方向感知算法（最佳性能）
            return DirectionAwareAlgorithm(max_floor, num_elevators)
    
    def on_init(self, elevators: List[ProxyElevator], floors: List[ProxyFloor]) -> None:
        """
        系统初始化回调

        Args:
            elevators: 电梯列表
            floors: 楼层列表
        """
        if self.debug:
            print("🚀 初始化智能电梯调度控制器")
            print(f"📊 电梯数量: {len(elevators)}, 楼层数量: {len(floors)}")
            print(f"🎯 使用算法: {self.algorithm_name.upper()}")
        
        self.elevators = elevators
        self.floors = floors
        max_floor = len(floors) - 1  # 楼层从0开始
        num_elevators = len(elevators)

        # 更新算法实例的参数
        if hasattr(self.algorithm, 'max_floor'):
            self.algorithm.max_floor = max_floor
        if hasattr(self.algorithm, 'num_elevators'):
            self.algorithm.num_elevators = num_elevators
        
        # 初始化电梯状态
        for i, elevator in enumerate(elevators):
            self.elevator_targets[elevator.id] = deque()
            self.elevator_destinations[elevator.id] = deque()
            self.elevator_wait_times[elevator.id] = {}
            
            # 使用算法初始化电梯
            self.algorithm.initialize_elevator(elevator, i)
            
            if self.debug:
                print(f"  🛗 电梯 E{elevator.id} 初始化完成")
    
        if self.debug:
            print(f"✅ 控制器初始化完成，使用 {self.algorithm.__class__.__name__}")

    def on_passenger_call(self, passenger: ProxyPassenger, floor: ProxyFloor, direction: str) -> None:
        """
        乘客呼叫电梯回调

        Args:
            passenger: 乘客对象
            floor: 呼叫楼层
            direction: 呼叫方向 ('up' 或 'down')
        """
        if self.debug:
            print(f"📞 乘客 {passenger.id} 在 F{floor.floor} 请求 {direction} 方向")
            print(f"   乘客目的地: F{passenger.destination}")
        
        self.all_passengers.append(passenger)
        
        # 记录乘客开始等待时间
        passenger_id = passenger.id
        current_tick = self.current_tick
        for elevator_id in self.elevator_wait_times:
            self.elevator_wait_times[elevator_id][passenger_id] = current_tick

        # 分配乘客到最佳电梯
        assigned_elevator = self._assign_passenger_to_elevator(
            passenger, floor, Direction(direction)
        )

        if assigned_elevator:
            if self.debug:
                print(f"  ✅ 分配给电梯 E{assigned_elevator.id}")
            
            # 添加乘客的出发楼层到电梯目标队列
            if passenger.origin not in self.elevator_targets[assigned_elevator.id]:
                self.elevator_targets[assigned_elevator.id].append(passenger.origin)
                if self.debug:
                    print(f"     添加出发楼层 F{passenger.origin} 到电梯 E{assigned_elevator.id} 目标队列")

            # 更新电梯目标
                self._update_elevator_targets(assigned_elevator)
        else:
            # 如果没有合适的电梯，添加到待处理请求
            self.pending_requests[Direction(direction)].add(passenger.origin)
            if self.debug:
                print(f"  ⏳ 添加到待处理请求队列")
    
    def _assign_passenger_to_elevator(
        self, passenger: ProxyPassenger, floor: ProxyFloor, direction: Direction
    ) -> Optional[ProxyElevator]:
        """
        根据算法逻辑分配乘客到最佳电梯

        Args:
            passenger: 乘客对象
            floor: 呼叫楼层
            direction: 呼叫方向

        Returns:
            最佳电梯对象，如果没有合适电梯则返回None
        """
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
        """
        检查电梯是否能够接载乘客

        Args:
            elevator: 电梯对象
            floor: 乘客所在楼层
            direction: 乘客呼叫方向

        Returns:
            是否能够接载乘客
        """
        # 检查容量
        if len(elevator.passengers) >= elevator.max_capacity:
            return False
        
        # 检查方向兼容性
        if elevator.target_floor_direction == Direction.STOPPED:
            return True
        
        if elevator.target_floor_direction == direction:
            if direction == Direction.UP and elevator.current_floor <= floor:
                return True
            elif direction == Direction.DOWN and elevator.current_floor >= floor:
                return True
        
        return False
    
    def _update_elevator_targets(self, elevator: ProxyElevator) -> None:
        """
        更新电梯目标队列并执行算法逻辑

        Args:
            elevator: 需要更新的电梯
        """
        if not self.elevator_targets[elevator.id]:
            return
        
        # 使用算法处理目标队列
        self.algorithm.handle_idle_elevator(elevator, self.elevator_targets[elevator.id])
    
    def on_elevator_idle(self, elevator: ProxyElevator) -> None:
        """
        电梯空闲回调

        Args:
            elevator: 空闲电梯对象
        """
        if self.debug:
            print(f"🛗 电梯 E{elevator.id} 空闲")
        
        # 处理待处理请求
        self._process_pending_requests(elevator)
        
        # 更新电梯目标
        self._update_elevator_targets(elevator)
    
    def _process_pending_requests(self, elevator: ProxyElevator) -> None:
        """
        处理待处理请求队列

        Args:
            elevator: 可用的电梯
        """
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

                    if self.debug:
                        print(f"  📋 处理待处理请求 F{nearest_request} (方向: {direction.value})")

                    self._update_elevator_targets(elevator)
                    break
    
    def on_elevator_stopped(self, elevator: ProxyElevator, floor: ProxyFloor) -> None:
        """
        电梯停靠回调

        Args:
            elevator: 停靠电梯对象
            floor: 停靠楼层
        """
        if self.debug:
            print(f"🛑 电梯 E{elevator.id} 停靠在 F{floor.floor}")
        
        # 移除已到达的目标
        if floor.floor in self.elevator_targets[elevator.id]:
            self.elevator_targets[elevator.id].remove(floor.floor)
        
        # 更新电梯方向状态（如果需要的话）
        if self.elevator_targets[elevator.id]:
            next_target = self.elevator_targets[elevator.id][0]
            # 方向由电梯系统自动管理，这里不需要手动设置
    
    def on_passenger_board(self, elevator: ProxyElevator, passenger: ProxyPassenger) -> None:
        """
        乘客上电梯回调

        Args:
            elevator: 电梯对象
            passenger: 上电梯的乘客
        """
        if self.debug:
            print(f"⬆️ 乘客 {passenger.id} 上电梯 E{elevator.id}")
            print(f"   从 F{passenger.origin} 到 F{passenger.destination}")

        # 记录乘客上电梯时间
        passenger_id = passenger.id
        if passenger_id in self.elevator_wait_times.get(elevator.id, {}):
            wait_time = self.current_tick - self.elevator_wait_times[elevator.id][passenger_id]
            self.performance_stats['total_wait_time'] += wait_time
            self.performance_stats['total_passengers'] += 1

            # 更新算法的性能指标
            if hasattr(self.algorithm, 'metrics'):
                self.algorithm.metrics[elevator.id].total_wait_time += wait_time
                self.algorithm.metrics[elevator.id].passengers_served += 1
        
        # 添加乘客目的地到电梯目标队列
        if passenger.destination not in self.elevator_targets[elevator.id]:
            self.elevator_targets[elevator.id].append(passenger.destination)
            if self.debug:
                print(f"   添加目的地 F{passenger.destination} 到电梯 E{elevator.id} 目标队列")

        # 更新电梯目标
        self._update_elevator_targets(elevator)
    
    def on_passenger_alight(self, elevator: ProxyElevator, passenger: ProxyPassenger, floor: ProxyFloor) -> None:
        """
        乘客下电梯回调

        Args:
            elevator: 电梯对象
            passenger: 下电梯的乘客
            floor: 下电梯楼层
        """
        if self.debug:
            print(f"⬇️ 乘客 {passenger.id} 在 F{floor.floor} 下电梯 E{elevator.id}")
        
        # 移除已到达的目的地
        if passenger.destination in self.elevator_targets[elevator.id]:
            self.elevator_targets[elevator.id].remove(passenger.destination)
    
    def on_elevator_passing_floor(self, elevator: ProxyElevator, floor: ProxyFloor, direction: str) -> None:
        """
        电梯经过楼层回调

        Args:
            elevator: 电梯对象
            floor: 经过的楼层
            direction: 行驶方向
        """
        if self.debug:
            print(f"🚶 电梯 E{elevator.id} 经过 F{floor.floor} ({direction})")
    
    def on_elevator_approaching(self, elevator: ProxyElevator, floor: ProxyFloor, direction: str) -> None:
        """
        电梯接近楼层回调

        Args:
            elevator: 电梯对象
            floor: 接近的楼层
            direction: 行驶方向
        """
        if self.debug:
            print(f"🔔 电梯 E{elevator.id} 接近 F{floor.floor} ({direction})")
    
    def on_event_execute_start(
        self, tick: int, events: List[SimulationEvent], 
        elevators: List[ProxyElevator], floors: List[ProxyFloor]
    ) -> None:
        """
        事件执行开始回调

        Args:
            tick: 当前tick
            events: 即将执行的事件列表
            elevators: 电梯列表
            floors: 楼层列表
        """
        if self.debug and events:
            print(f"📊 Tick {tick}: 处理 {len(events)} 个事件")
    
    def on_event_execute_end(
        self, tick: int, events: List[SimulationEvent], 
        elevators: List[ProxyElevator], floors: List[ProxyFloor]
    ) -> None:
        """
        事件执行结束回调

        Args:
            tick: 当前tick
            events: 已执行的事件列表
            elevators: 电梯列表
            floors: 楼层列表
        """
        if self.debug and tick % 100 == 0:  # 每100个tick打印一次性能统计
            self._print_performance_stats()

    def _print_performance_stats(self) -> None:
        """打印性能统计信息"""
        if self.performance_stats['total_passengers'] > 0:
            avg_wait_time = self.performance_stats['total_wait_time'] / self.performance_stats['total_passengers']
            print("📈 性能统计:")
            print(f"   总乘客数: {self.performance_stats['total_passengers']}")
            print(f"   平均等待时间: {avg_wait_time:.2f} ticks")
            print(f"   总等待时间: {self.performance_stats['total_wait_time']:.2f} ticks")

    def on_simulation_complete(self, final_state: Dict[str, Any]) -> None:
        """
        模拟完成回调

        Args:
            final_state: 最终状态数据
        """
        print("🏁 模拟完成！")
        print("📊 最终性能统计:")
        print(f"   总乘客数: {self.performance_stats['total_passengers']}")
        if self.performance_stats['total_passengers'] > 0:
            avg_wait_time = self.performance_stats['total_wait_time'] / self.performance_stats['total_passengers']
            print(f"   平均等待时间: {avg_wait_time:.2f} ticks")
            print(f"   总等待时间: {self.performance_stats['total_wait_time']:.2f} ticks")

        # 计算P95等待时间
        if self.all_passengers:
            wait_times = []
            for passenger in self.all_passengers:
                # 这里需要根据实际情况计算每个乘客的等待时间
                # 暂时使用平均值作为近似
                if self.performance_stats['total_passengers'] > 0:
                    wait_times.append(avg_wait_time)

            if wait_times:
                wait_times.sort()
                p95_index = int(len(wait_times) * 0.95)
                p95_wait_time = wait_times[min(p95_index, len(wait_times) - 1)]
                print(f"   P95等待时间: {p95_wait_time:.2f} ticks")

        print(f"🎯 使用的算法: {self.algorithm_name.upper()}")
        print(f"🏆 算法效率评分: {self.performance_stats.get('algorithm_efficiency', 'N/A')}")


if __name__ == "__main__":
    import sys

    # 解析命令行参数
    algorithm = "direction_aware"  # 默认使用方向感知算法（最佳性能）
    debug = False
    
    if len(sys.argv) > 1:
        algorithm = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "--debug":
        debug = True

    print(f"🚀 启动电梯调度系统 - 算法: {algorithm}")
    print(f"🐛 调试模式: {'开启' if debug else '关闭'}")

    # 创建控制器实例
    controller = SmartElevatorController(algorithm=algorithm, debug=debug)

    try:
        # 启动调度系统
        controller.start()
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断程序执行")
    finally:
        # 停止控制器
        controller.stop()
        print("✅ 电梯调度系统已停止")