<template>
  <div style="display:flex; flex-direction:column; gap:4px; padding:12px; border:1px solid #ccc;">
    <div v-for="floor in floorList" :key="floor" style="position:relative; height:50px; border-bottom:1px solid #eee;">
      <!-- 楼层号 -->
      <span style="position:absolute; left:0; top:50%; transform:translateY(-50%)">
        F{{ floor }}
      </span>

      <!-- 楼层队列：紧挨电梯组左侧 -->
      <div v-if="queues[floor-1]"
           :style="{ position:'absolute', right:(groupWidth + 8) + 'px', top:'50%', transform:'translateY(-50%)' }">
        <FloorQueueBadge :count="queues[floor-1]?.waiting ?? 0" />
      </div>

      <!-- 队列与电梯之间的分隔线 -->
      <div :style="{
            position:'absolute',
            right:(groupWidth + 4) + 'px',
            top:'50%',
            transform:'translateY(-50%)',
            width:'1px',
            height:'40px',
            background:'#e5e7eb'
          }" />

      <!-- 电梯 -->
      <!-- 右侧电梯组容器 -->
      <div :style="{ position:'absolute', right:'0', top:'50%', transform:'translateY(-50%)', height:'40px', width: groupWidth + 'px' }">
        <template v-for="e in elevators" :key="e.id">
          <ElevatorCar v-if="e.floor === floor" :id="e.id" />
        </template>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive } from 'vue';
import type { Elevator, FloorQueue } from '../types';
import { ElevatorStatus } from '../types';
import ElevatorCar from './ElevatorCar.vue';
import FloorQueueBadge from './FloorQueueBadge.vue';

export default defineComponent({
  components: { ElevatorCar, FloorQueueBadge },
  setup() {
    const floors = 10; // 楼层数
    const floorList = Array.from({ length: floors }, (_, i) => floors - i);
    const elevators: Elevator[] = reactive([
      { id: 0, floor: 1, status: ElevatorStatus.STOPPED },
      { id: 1, floor: 1, status: ElevatorStatus.STOPPED },
      { id: 2, floor: 1, status: ElevatorStatus.STOPPED },
    ]);

    const queues: FloorQueue[] = reactive(
      Array.from({ length: floors }, (_, i) => ({ floor: i+1, waiting: 0 }))
    );

    const carWidth = 24;
    const carGap = 6;
    const groupWidth = elevators.length * carWidth + Math.max(0, elevators.length - 1) * carGap + 6;

    return { floors, floorList, elevators, queues, groupWidth };
  }
});
</script>

<style scoped>
/* 可以在这里加全局极简样式 */
</style>
