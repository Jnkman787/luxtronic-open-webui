<script lang="ts">
	import { onMount } from 'svelte';

	export let title: string = '';
	export let subtitle: string = '';
	export let labels: string[] = [];
	export let series: Array<{ name: string; values: number[]; color: string }> = [];
	export let isDark: boolean = false;
	export let height: number = 200;
	export let showGrid: boolean = true;
	export let showDots: boolean = false;
	export let showLegend: boolean = true;
	export let fillGaps: boolean = true;

	let containerWidth = 800;
	let container: HTMLDivElement;

	// Chart dimensions
	const padding = { top: 20, right: 20, bottom: 30, left: 50 };

	$: chartWidth = Math.max(0, containerWidth - padding.left - padding.right);
	$: chartHeight = Math.max(0, height - padding.top - padding.bottom);

	// Calculate scales across all series
	$: allValues = series.flatMap((s) => s.values.filter((v) => v !== null && v !== undefined));
	$: minValue = allValues.length > 0 ? Math.min(...allValues, 0) : 0;
	$: maxValue = allValues.length > 0 ? Math.max(...allValues, 1) : 1;
	$: valueRange = maxValue - minValue || 1;

	// Scale functions
	$: xScale = (index: number) => (index / (labels.length - 1 || 1)) * chartWidth;
	$: yScale = (value: number) => chartHeight - ((value - minValue) / valueRange) * chartHeight;

	// Generate path for each series (skip null/undefined values for gap filling)
	function generatePath(values: number[]): string {
		if (values.length === 0) return '';

		const points: Array<{ x: number; y: number }> = [];
		for (let i = 0; i < values.length; i++) {
			const v = values[i];
			if (v !== null && v !== undefined && !isNaN(v)) {
				points.push({ x: xScale(i), y: yScale(v) });
			}
		}

		if (points.length === 0) return '';

		return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
	}

	// Y-axis ticks
	$: yTicks = Array.from({ length: 5 }, (_, i) => {
		const value = minValue + (valueRange * (4 - i)) / 4;
		return { value, y: yScale(value) };
	});

	// X-axis labels (show first, middle, last)
	$: xLabels =
		labels.length > 0
			? [
					{ index: 0, label: formatDate(labels[0]) },
					{ index: Math.floor(labels.length / 2), label: formatDate(labels[Math.floor(labels.length / 2)]) },
					{ index: labels.length - 1, label: formatDate(labels[labels.length - 1]) }
				]
			: [];

	function formatDate(dateStr: string | undefined): string {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		if (isNaN(date.getTime())) return dateStr.substring(0, 10);
		return `${date.getMonth() + 1}/${date.getDate()}`;
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
					<div class="w-3 h-3 rounded-sm" style="background-color: {s.color}"></div>
					<span class="text-xs {isDark ? 'text-gray-400' : 'text-gray-600'}">{s.name}</span>
				</div>
			{/each}
		</div>
	{/if}

	<svg width="100%" {height} class="overflow-visible">
		<defs>
			{#each series as s, idx}
				<linearGradient id="areaGradient-{idx}-{title.replace(/\s+/g, '')}" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0%" stop-color={s.color} stop-opacity="0.2" />
					<stop offset="100%" stop-color={s.color} stop-opacity="0" />
				</linearGradient>
			{/each}
		</defs>

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

			<!-- Lines for each series -->
			{#each series as s, idx}
				{@const pathD = generatePath(s.values)}
				{#if pathD}
					<path d={pathD} fill="none" stroke={s.color} stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
				{/if}

				<!-- Dots -->
				{#if showDots && s.values.length > 0}
					{#each s.values as value, i}
						{#if value !== null && value !== undefined && !isNaN(value)}
							<circle cx={xScale(i)} cy={yScale(value)} r="3" fill={s.color} />
						{/if}
					{/each}
				{/if}
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
