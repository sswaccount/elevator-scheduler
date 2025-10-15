<template>
  <div class="queue-badge" :style="badgeStyle">
    {{ count }}
  </div>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue';
import type { CSSProperties } from 'vue';

export default defineComponent({
  name: 'FloorQueueBadge',
  props: {
    count: { type: Number, required: true },
  },
  setup() {
    const badgeStyle = computed<CSSProperties>(() => ({
      width: '20px',
      height: '20px',
      borderRadius: '50%',
      background: '#aaa', // 目前保持灰色，后续可根据人数/等待时长动态变色
      textAlign: 'center',
      lineHeight: '20px',
      color: '#fff',
      fontSize: '12px',
      userSelect: 'none'
    }));

    return { badgeStyle };
  }
});
</script>

<style scoped>
</style>


