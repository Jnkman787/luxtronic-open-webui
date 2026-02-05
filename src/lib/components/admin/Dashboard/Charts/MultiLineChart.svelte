<script lang="ts">
	import type { TimeSeriesPoint } from '$lib/apis/dashboard';
	import { onMount } from 'svelte';

	export type LineSeries = {
		label: string;
		color: string;
		data: TimeSeriesPoint[];
	};

	export let title: string = '';
	export let subtitle: string = '';
	export let series: LineSeries[] = [];
	export let isDark: boolean = false;
	export let height: number = 200;
	export let showGrid: boolean = true;
	export let showDots: boolean = false;
	export let showLines: boolean = true;
	export let xLabelMode: 'auto' | 'date' | 'time' = 'auto';

	let containerWidth = 800;
	let container: HTMLDivElement;

	const padding = { top: 20, right: 20, bottom: 30, left: 50 };

	$: chartWidth = containerWidth - padding.left - padding.right;
	$: chartHeight = height - padding.top - padding.bottom;

	$: allValues = series.flatMap((s) => s.data.map((d) => d.value));
	$: minValue = Math.min(...allValues, 0);
	$: maxValue = Math.max(...allValues, 1);
	$: valueRange = maxValue - minValue || 1;

	$: baseSeries = series[0]?.data || [];
	$: uniqueDays = new Set(baseSeries.map((d) => new Date(d.time).toDateString()));
	$: resolvedLabelMode =
		xLabelMode === 'auto' ? (uniqueDays.size > 1 ? 'date' : 'time') : xLabelMode;
	$: xScale = (index: number, count: number) => (index / (count - 1 || 1)) * chartWidth;
	$: yScale = (value: number) => chartHeight - ((value - minValue) / valueRange) * chartHeight;

	$: yTicks = Array.from({ length: 5 }, (_, i) => {
		const value = minValue + (valueRange * (4 - i)) / 4;
		return { value, y: yScale(value) };
	});

	$: xLabels =
		baseSeries.length > 0
			? [
					{ index: 0, label: formatLabel(baseSeries[0]?.time) },
					{
						index: Math.floor(baseSeries.length / 2),
						label: formatLabel(baseSeries[Math.floor(baseSeries.length / 2)]?.time)
					},
					{
						index: baseSeries.length - 1,
						label: formatLabel(baseSeries[baseSeries.length - 1]?.time)
					}
				]
			: [];

	function formatLabel(dateStr: string | undefined): string {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		if (resolvedLabelMode === 'time') {
			return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
		}
		return `${date.getMonth() + 1}/${date.getDate()}`;
	}

	function formatValue(value: number): string {
		if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
		if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
		return value.toFixed(0);
	}

	function buildPath(data: TimeSeriesPoint[]): string {
		if (data.length === 0) return '';
		return data
			.map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i, data.length)} ${yScale(d.value)}`)
			.join(' ');
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
	{#if title || subtitle || series.length > 0}
		<div class="mb-2 flex flex-col gap-1">
			{#if title}
				<h3 class="text-sm font-semibold {isDark ? 'text-white' : 'text-gray-900'}">{title}</h3>
			{/if}
			{#if subtitle}
				<p class="text-xs {isDark ? 'text-gray-400' : 'text-gray-500'}">{subtitle}</p>
			{/if}
			{#if series.length > 1}
				<div class="flex flex-wrap gap-2 text-xs">
					{#each series as line}
						<span class="flex items-center gap-1 {isDark ? 'text-gray-300' : 'text-gray-600'}">
							<span class="inline-block w-2 h-2 rounded-full" style="background:{line.color}"></span>
							{line.label}
						</span>
					{/each}
				</div>
			{/if}
		</div>
	{/if}

	<svg width="100%" {height} class="overflow-visible">
		<g transform="translate({padding.left}, {padding.top})">
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

			{#each xLabels as label}
				<text
					x={xScale(label.index, baseSeries.length || 1)}
					y={chartHeight + 20}
					text-anchor="middle"
					class="text-xs {isDark ? 'fill-gray-400' : 'fill-gray-500'}"
				>
					{label.label}
				</text>
			{/each}

			{#if series.length === 0}
				<text
					x={chartWidth / 2}
					y={chartHeight / 2}
					text-anchor="middle"
					dominant-baseline="middle"
					class="text-sm {isDark ? 'fill-gray-500' : 'fill-gray-400'}"
				>
					No data available
				</text>
			{:else}
				{#each series as line}
					{#if line.data.length > 0}
						{#if showLines}
							<path
								d={buildPath(line.data)}
								fill="none"
								stroke={line.color}
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							/>
						{/if}
						{#if showDots}
							{#each line.data as point, i}
								<circle
									cx={xScale(i, line.data.length)}
									cy={yScale(point.value)}
									r="3"
									fill={line.color}
								/>
							{/each}
						{/if}
					{/if}
				{/each}
			{/if}
		</g>
	</svg>
</div>
