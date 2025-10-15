<template>
  <div :style="styleObject">
    {{ id }}
  </div>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue';
import type { CSSProperties } from 'vue';

export default defineComponent({
  name: 'ElevatorCar',
  props: {
    id: { type: Number, required: true },
  },
  setup(props) {
    const styleObject = computed<CSSProperties>(() => ({
      position: 'absolute',
      right: (props.id * 30) + 'px',
      width: '24px',
      height: '40px',
      background: `hsl(${(props.id * 70) % 360} 60% 60%)`,
      borderRadius: '4px',
      textAlign: 'center',
      lineHeight: '40px',
      color: '#fff'
    }));

    return { styleObject };
  }
});
</script>

<style scoped>
</style>


