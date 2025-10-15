<template>
  <div>
    <h1>电梯调度模拟</h1>
    <ControlBar
      :selectedAlgorithm="selectedAlgorithm"
      :selectedDataset="selectedDataset"
      :isRunning="isRunning"
      :isPaused="isPaused"
      :speed="speed"
      @update:selectedAlgorithm="v => selectedAlgorithm = v as any"
      @update:selectedDataset="v => selectedDataset = v as any"
      @update:speed="v => speed = Number(v)"
      @start="onStart"
      @pause="onPause"
      @stop="onStop"
    />
    <ElevatorView />
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue';
import ElevatorView from './components/ElevatorView.vue';
import ControlBar from './components/ControlBar.vue';

export default defineComponent({
  components: { ElevatorView, ControlBar },
  setup() {
    const selectedAlgorithm = ref<'fcfs' | 'sstf' | 'look'>('fcfs');
    const selectedDataset = ref<'sampleA' | 'sampleB' | 'realtime'>('sampleA');
    const isRunning = ref(false);
    const isPaused = ref(false);
    const speed = ref<number>(1);

    const onStart = () => {
      isRunning.value = true;
      isPaused.value = false;
      // 占位：这里可以发事件或调用控制逻辑
      console.log('start', { algorithm: selectedAlgorithm.value, dataset: selectedDataset.value, speed: speed.value });
    };

    const onPause = () => {
      if (!isRunning.value) return;
      isPaused.value = !isPaused.value;
      console.log(isPaused.value ? 'pause' : 'resume');
    };

    const onStop = () => {
      isRunning.value = false;
      isPaused.value = false;
      // 占位：这里可以发事件或调用控制逻辑
      console.log('stop');
    };

    return { selectedAlgorithm, selectedDataset, isRunning, isPaused, speed, onStart, onPause, onStop };
  }
});
</script>

<style scoped>
</style>
