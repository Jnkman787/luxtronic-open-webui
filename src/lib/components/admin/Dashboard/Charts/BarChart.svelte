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
	export let stacked: boolean = false;

	let containerWidth = 800;
	let container: HTMLDivElement;

	// Chart dimensions
	const padding = { top: 20, right: 20, bottom: 40, left: 50 };

	$: chartWidth = Math.max(0, containerWidth - padding.left - padding.right);
	$: chartHeight = Math.max(0, height - padding.top - padding.bottom);

	// Calculate scales
	$: allValues = stacked
		? labels.map((_, i) => series.reduce((sum, s) => sum + (s.values[i] || 0), 0))
		: series.flatMap((s) => s.values.filter((v) => v !== null && v !== undefined));
	$: maxValue = allValues.length > 0 ? Math.max(...allValues, 1) : 1;

	// Bar dimensions
	$: groupWidth = labels.length > 0 ? chartWidth / labels.length : 20;
	$: barWidth = stacked
		? Math.max(4, groupWidth * 0.7)
		: Math.max(4, (groupWidth * 0.8) / series.length);
	$: groupPadding = groupWidth * 0.1;

	// Scale functions
	$: xScale = (index: number) => index * groupWidth + groupWidth / 2;
	$: yScale = (value: number) => chartHeight - (value / maxValue) * chartHeight;
	$: barHeight = (value: number) => (value / maxValue) * chartHeight;

	// Y-axis ticks
	$: yTicks = Array.from({ length: 5 }, (_, i) => {
		const value = (maxValue * (4 - i)) / 4;
		return { value, y: yScale(value) };
	});

	// X-axis labels (show subset if too many)
	$: xLabels =
		labels.length <= 10
			? labels.map((label, index) => ({ index, label: formatLabel(label) }))
			: [
					{ index: 0, label: formatLabel(labels[0]) },
					{ index: Math.floor(labels.length / 2), label: formatLabel(labels[Math.floor(labels.length / 2)]) },
					{ index: labels.length - 1, label: formatLabel(labels[labels.length - 1]) }
				];

	function formatLabel(label: string): string {
		if (!label) return '';
		// Try to parse as date
		const date = new Date(label);
		if (!isNaN(date.getTime())) {
			return `${date.getMonth() + 1}/${date.getDate()}`;
		}
		// Truncate long labels
		return label.length > 10 ? label.substring(0, 10) + '...' : label;
	}

	function formatValue(value: number): string {
		if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
		if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
		return value.toFixed(0);
	}

	// Get bar position for grouped bars
	function getBarX(labelIndex: number, seriesIndex: number): number {
		if (stacked) {
			return xScale(labelIndex) - barWidth / 2;
		}
		const totalBarsWidth = barWidth * series.length;
		const startX = xScale(labelIndex) - totalBarsWidth / 2;
		return startX + seriesIndex * barWidth;
	}

	// Get bar Y position for stacked bars
	function getBarY(labelIndex: number, seriesIndex: number): number {
		if (!stacked) {
			return yScale(series[seriesIndex].values[labelIndex] || 0);
		}
		// Sum all values below this series
		let sum = 0;
		for (let i = 0; i <= seriesIndex; i++) {
			sum += series[i].values[labelIndex] || 0;
		}
		return yScale(sum);
	}

	// Get bar height for stacked bars
	function getBarHeight(labelIndex: number, seriesIndex: number): number {
		const value = series[seriesIndex].values[labelIndex] || 0;
		return barHeight(value);
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
	{#if showLegend && series.length > 1}
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
				<linearGradient id="barGradient-{idx}-{title.replace(/\s+/g, '')}" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0%" stop-color={s.color} stop-opacity="0.9" />
					<stop offset="100%" stop-color={s.color} stop-opacity="0.7" />
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

			<!-- Bars -->
			{#if labels.length > 0 && series.length > 0}
				{#each labels as _, labelIndex}
					{#each series as s, seriesIndex}
						{@const value = s.values[labelIndex] || 0}
						{#if value > 0}
							<rect
								x={getBarX(labelIndex, seriesIndex)}
								y={getBarY(labelIndex, seriesIndex)}
								width={barWidth}
								height={getBarHeight(labelIndex, seriesIndex)}
								fill="url(#barGradient-{seriesIndex}-{title.replace(/\s+/g, '')})"
								rx="2"
							/>
						{/if}
					{/each}
				{/each}
			{/if}

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
