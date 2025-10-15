<template>
  <div class="control-bar">
    <div class="control-group">
      <span class="control-label">算法</span>
      <select class="control-select" :value="selectedAlgorithm" @change="onAlgChange">
        <option value="fcfs">先来先服务</option>
        <option value="sstf">最短等待</option>
        <option value="look">LOOK</option>
      </select>
    </div>

    <div class="control-group">
      <span class="control-label">数据</span>
      <select class="control-select" :value="selectedDataset" @change="onDatasetChange">
        <option value="sampleA">示例A</option>
        <option value="sampleB">示例B</option>
        <option value="realtime">实时</option>
      </select>
    </div>

    <div class="control-group">
      <button class="btn" @click="$emit('start')" :disabled="isRunning">开始</button>
      <button class="btn" @click="$emit('pause')" :disabled="!isRunning">{{ isPaused ? '继续' : '停止' }}</button>
      <button class="btn btn-secondary" @click="$emit('stop')" :disabled="!isRunning && !isPaused">结束</button>
    </div>

    <div class="control-group">
      <span class="control-label">倍速</span>
      <select class="control-select" :value="speed" @change="onSpeedChange">
        <option :value="0.5">0.5x</option>
        <option :value="1">1x</option>
        <option :value="2">2x</option>
        <option :value="4">4x</option>
      </select>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'ControlBar',
  props: {
    selectedAlgorithm: { type: String, required: true },
    selectedDataset: { type: String, required: true },
    isRunning: { type: Boolean, required: true },
    isPaused: { type: Boolean, required: true },
    speed: { type: Number, required: true }
  },
  emits: ['update:selectedAlgorithm', 'update:selectedDataset', 'update:speed', 'start', 'pause', 'stop'],
  setup(_, { emit }) {
    const onAlgChange = (e: Event) => {
      const value = (e.target as HTMLSelectElement).value as 'fcfs' | 'sstf' | 'look';
      emit('update:selectedAlgorithm', value);
    };
    const onDatasetChange = (e: Event) => {
      const value = (e.target as HTMLSelectElement).value as 'sampleA' | 'sampleB' | 'realtime';
      emit('update:selectedDataset', value);
    };
    const onSpeedChange = (e: Event) => {
      const value = Number((e.target as HTMLSelectElement).value);
      emit('update:speed', value);
    };
    return { onAlgChange, onDatasetChange, onSpeedChange };
  }
});
</script>

<style scoped>
.control-bar {
  display: flex;
  gap: 16px;
  align-items: center;
  justify-content: center;
  margin: 12px auto 16px;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  background: linear-gradient(180deg, #ffffff, #fafafa);
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

.control-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

.control-label {
  font-size: 12px;
  color: #6b7280;
}

.control-select {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  position: relative;
  padding: 6px 28px 6px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #ffffff;
  color: #111827;
  font-size: 14px;
  line-height: 1.2;
  box-shadow: inset 0 1px 0 rgba(0,0,0,0.02);
}

.control-select:focus {
  outline: none;
  border-color: #93c5fd;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.2);
}

.btn {
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  color: #111827;
  font-size: 14px;
  line-height: 1.2;
  cursor: pointer;
  transition: box-shadow 0.15s ease, transform 0.05s ease;
}

.btn:hover {
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.btn:active {
  transform: translateY(1px);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f9fafb;
}
</style>


