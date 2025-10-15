export enum Direction {
  UP = 'up',
  DOWN = 'down',
  STOPPED = 'stopped',
}

export enum PassengerStatus {
  WAITING = 'waiting',
  IN_ELEVATOR = 'in_elevator',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

export enum ElevatorStatus {
  START_UP = 'start_up',
  START_DOWN = 'start_down',
  CONSTANT_SPEED = 'constant_speed',
  STOPPED = 'stopped',
}

export enum EventType {
  UP_BUTTON_PRESSED = 'up_button_pressed',
  DOWN_BUTTON_PRESSED = 'down_button_pressed',
  PASSING_FLOOR = 'passing_floor',
  STOPPED_AT_FLOOR = 'stopped_at_floor',
  ELEVATOR_APPROACHING = 'elevator_approaching',
  IDLE = 'idle',
  PASSENGER_BOARD = 'passenger_board',
  PASSENGER_ALIGHT = 'passenger_alight',
  ELEVATOR_MOVE = 'elevator_move',
}

// 具体 elevator state
export type Elevator = {
  id: number;
  // 当前“离散”楼层（后端可能上报整数floor表示最近的楼层）
  floor: number;
  // 分数位置：0..1 表示在 floor -> floor+1 之间（可选，后端可上报）
  posFraction?: number;
  // 目标楼层（如果有）
  targetFloor?: number | null;
  // 实际运动方向（后端或前端计算）
  direction?: Direction;
  // 更细的运行状态机（后端 ElevatorStatus）
  status?: ElevatorStatus;
  passengerCount?: number;
  // 可选：速度（m/s 或抽象 单位/s）
  speed?: number;
  // 门状态（可选：open/closed）
  doorOpen?: boolean;
};

// 每层队列信息
export type FloorQueue = {
  floor: number;
  waiting: number;
  // 可选：最长等待时间 / 平均等待时间
  maxWaitMs?: number;
  avgWaitMs?: number;
};

// 完整快照（后端推送或回放帧）
export type AppState = {
  time: number; // unix ms
  elevators: Elevator[];
  queues: FloorQueue[];
  // 可选：事件数组
  events?: { type: EventType; elevatorId?: number; floor?: number; ts?: number; meta?: any }[];
};