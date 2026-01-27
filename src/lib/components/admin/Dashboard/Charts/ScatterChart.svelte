<script lang="ts">
	import { onMount } from 'svelte';

	export let title: string = '';
	export let subtitle: string = '';
	export let labels: string[] = [];
	export let series: Array<{ name: string; values: number[]; color: string }> = [];
	export let isDark: boolean = false;
	export let height: number = 200;
	export let showGrid: boolean = true;
	export let showLegend: boolean = true;
	export let dotSize: number = 5;

	let containerWidth = 800;
	let container: HTMLDivElement;

	// Chart dimensions
	const padding = { top: 20, right: 20, bottom: 30, left: 50 };

	$: chartWidth = containerWidth - padding.left - padding.right;
	$: chartHeight = height - padding.top - padding.bottom;

	// Calculate scales across all series
	$: allValues = series.flatMap((s) => s.values.filter((v) => v !== null && v !== undefined));
	$: minValue = allValues.length > 0 ? Math.min(...allValues, 0) : 0;
	$: maxValue = allValues.length > 0 ? Math.max(...allValues, 1) : 1;
	$: valueRange = maxValue - minValue || 1;

	// Scale functions
	$: xScale = (index: number) => (index / (labels.length - 1 || 1)) * chartWidth;
	$: yScale = (value: number) => chartHeight - ((value - minValue) / valueRange) * chartHeight;

	// Y-axis ticks
	$: yTicks = Array.from({ length: 5 }, (_, i) => {
		const value = minValue + (valueRange * (4 - i)) / 4;
		return { value, y: yScale(value) };
	});

	// X-axis labels (show first, middle, last)
	$: xLabels =
		labels.length > 0
			? [
					{ index: 0, label: formatLabel(labels[0]) },
					{ index: Math.floor(labels.length / 2), label: formatLabel(labels[Math.floor(labels.length / 2)]) },
					{ index: labels.length - 1, label: formatLabel(labels[labels.length - 1]) }
				]
			: [];

	function formatLabel(label: string): string {
		if (!label) return '';
		const date = new Date(label);
		if (!isNaN(date.getTime())) {
			return `${date.getMonth() + 1}/${date.getDate()}`;
		}
		return label.length > 10 ? label.substring(0, 10) + '...' : label;
	}

	function formatValue(value: number): string {
		if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
		if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
		return value.toFixed(0);
	}

	onMount(() => {
		if (container) {
			const resizeObserver = new ResizeObserver((entries) => {
				containerWidth = entries[0].contentRect.width;
			});
			resizeObserver.observe(container);
			return () => resizeObserver.disconnect();
		}
	});
</script>

<div class="w-full" bind:this={container}>
	{#if title || subtitle}
		<div class="mb-2">
			{#if title}
				<h3 class="text-sm font-semibold {isDark ? 'text-white' : 'text-gray-900'}">{title}</h3>
			{/if}
			{#if subtitle}
				<p class="text-xs {isDark ? 'text-gray-400' : 'text-gray-500'}">{subtitle}</p>
			{/if}
		</div>
	{/if}

	<!-- Legend -->
	{#if showLegend && series.length > 0}
		<div class="flex flex-wrap gap-3 mb-2">
			{#each series as s}
				<div class="flex items-center gap-1.5">
					<div class="w-3 h-3 rounded-full" style="background-color: {s.color}"></div>
					<span class="text-xs {isDark ? 'text-gray-400' : 'text-gray-600'}">{s.name}</span>
				</div>
			{/each}
		</div>
	{/if}

	<svg width="100%" {height} class="overflow-visible">
		<g transform="translate({padding.left}, {padding.top})">
			<!-- Grid lines -->
			{#if showGrid}
				{#each yTicks as tick}
					<line
						x1="0"
						y1={tick.y}
						x2={chartWidth}
						y2={tick.y}
						stroke={isDark ? '#374151' : '#e5e7eb'}
						stroke-dasharray="4"
					/>
				{/each}
			{/if}

			<!-- Y-axis labels -->
			{#each yTicks as tick}
				<text
					x="-8"
					y={tick.y}
					text-anchor="end"
					dominant-baseline="middle"
					class="text-xs {isDark ? 'fill-gray-400' : 'fill-gray-500'}"
				>
					{formatValue(tick.value)}
				</text>
			{/each}

			<!-- X-axis labels -->
			{#each xLabels as label}
				<text
					x={xScale(label.index)}
					y={chartHeight + 20}
					text-anchor="middle"
					class="text-xs {isDark ? 'fill-gray-400' : 'fill-gray-500'}"
				>
					{label.label}
				</text>
			{/each}

			<!-- Scatter points for each series -->
			{#each series as s}
				{#each s.values as value, i}
					{#if value !== null && value !== undefined && !isNaN(value)}
						<circle
							cx={xScale(i)}
							cy={yScale(value)}
							r={dotSize}
							fill={s.color}
							fill-opacity="0.7"
							stroke={s.color}
							stroke-width="1"
						/>
					{/if}
				{/each}
			{/each}

			<!-- No data message -->
			{#if labels.length === 0 || series.length === 0}
				<text
					x={chartWidth / 2}
					y={chartHeight / 2}
					text-anchor="middle"
					dominant-baseline="middle"
					class="text-sm {isDark ? 'fill-gray-500' : 'fill-gray-400'}"
				>
					No data available
				</text>
			{/if}
		</g>
	</svg>
</div>
