<script lang="ts">
	import { onMount } from 'svelte';

	export let title: string = '';
	export let subtitle: string = '';
	export let labels: string[] = [];
	export let series: Array<{ name: string; values: number[]; color: string }> = [];
	export let isDark: boolean = false;
	export let height: number = 250;
	export let showLegend: boolean = true;
	export let showLabels: boolean = true;
	export let donut: boolean = false;

	let containerWidth = 400;
	let container: HTMLDivElement;

	// For pie charts, we use the first value from each series
	// OR if we have one series with multiple values, use those
	$: pieData =
		series.length > 0 && series[0].values.length > 1
			? labels.map((label, i) => ({
					name: label,
					value: series[0].values[i] || 0,
					color: getColor(i)
				}))
			: series.map((s, i) => ({
					name: s.name,
					value: s.values[0] || 0,
					color: s.color
				}));

	// Default color palette if we need to generate colors
	const defaultColors = [
		'#5CC9D3',
		'#B96A6A',
		'#F9A620',
		'#8B5CF6',
		'#10B981',
		'#EC4899',
		'#F59E0B',
		'#6366F1'
	];

	function getColor(index: number): string {
		if (series.length > 0 && series[0]?.color) {
			// Try to use series colors if available
			return series[index % series.length]?.color || defaultColors[index % defaultColors.length];
		}
		return defaultColors[index % defaultColors.length];
	}

	// Calculate dimensions
	$: svgWidth = Math.max(0, Math.min(containerWidth, height));
	$: chartSize = Math.min(containerWidth, height - 40);
	$: radius = chartSize / 2 - 20;
	$: innerRadius = donut ? radius * 0.6 : 0;
	$: centerX = svgWidth / 2;
	$: centerY = height / 2;

	// Calculate total and percentages
	$: total = pieData.reduce((sum, d) => sum + d.value, 0);

	// Generate arc paths
	$: arcs = calculateArcs(pieData, total);

	function calculateArcs(
		data: Array<{ name: string; value: number; color: string }>,
		totalValue: number
	): Array<{
		path: string;
		color: string;
		name: string;
		value: number;
		percentage: number;
		labelX: number;
		labelY: number;
		midAngle: number;
	}> {
		if (totalValue === 0) return [];

		const result = [];
		let currentAngle = -Math.PI / 2; // Start from top

		for (const item of data) {
			const percentage = (item.value / totalValue) * 100;
			const angle = (item.value / totalValue) * 2 * Math.PI;
			const endAngle = currentAngle + angle;

			// Calculate path
			const largeArc = angle > Math.PI ? 1 : 0;
			const x1 = centerX + radius * Math.cos(currentAngle);
			const y1 = centerY + radius * Math.sin(currentAngle);
			const x2 = centerX + radius * Math.cos(endAngle);
			const y2 = centerY + radius * Math.sin(endAngle);

			let path: string;
			if (innerRadius > 0) {
				// Donut chart
				const ix1 = centerX + innerRadius * Math.cos(currentAngle);
				const iy1 = centerY + innerRadius * Math.sin(currentAngle);
				const ix2 = centerX + innerRadius * Math.cos(endAngle);
				const iy2 = centerY + innerRadius * Math.sin(endAngle);
				path = `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} L ${ix2} ${iy2} A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${ix1} ${iy1} Z`;
			} else {
				// Pie chart
				path = `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;
			}

			// Calculate label position
			const midAngle = currentAngle + angle / 2;
			const labelRadius = donut ? (radius + innerRadius) / 2 : radius * 0.65;
			const labelX = centerX + labelRadius * Math.cos(midAngle);
			const labelY = centerY + labelRadius * Math.sin(midAngle);

			result.push({
				path,
				color: item.color,
				name: item.name,
				value: item.value,
				percentage,
				labelX,
				labelY,
				midAngle
			});

			currentAngle = endAngle;
		}

		return result;
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

	<div class="flex flex-col md:flex-row items-center gap-4">
		<svg width={svgWidth} {height} class="overflow-visible flex-shrink-0">
			{#if arcs.length > 0}
				{#each arcs as arc}
					<path d={arc.path} fill={arc.color} stroke={isDark ? '#1f2937' : '#ffffff'} stroke-width="2" />
				{/each}

				<!-- Labels inside slices -->
				{#if showLabels}
					{#each arcs as arc}
						{#if arc.percentage >= 5}
							<text
								x={arc.labelX}
								y={arc.labelY}
								text-anchor="middle"
								dominant-baseline="middle"
								class="text-xs font-medium fill-white"
								style="text-shadow: 0 1px 2px rgba(0,0,0,0.5)"
							>
								{arc.percentage.toFixed(0)}%
							</text>
						{/if}
					{/each}
				{/if}

				<!-- Center label for donut -->
				{#if donut && total > 0}
					<text
						x={centerX}
						y={centerY - 8}
						text-anchor="middle"
						dominant-baseline="middle"
						class="text-sm font-semibold {isDark ? 'fill-white' : 'fill-gray-900'}"
					>
						{formatValue(total)}
					</text>
					<text
						x={centerX}
						y={centerY + 8}
						text-anchor="middle"
						dominant-baseline="middle"
						class="text-xs {isDark ? 'fill-gray-400' : 'fill-gray-500'}"
					>
						Total
					</text>
				{/if}
			{:else}
				<text
					x={centerX}
					y={centerY}
					text-anchor="middle"
					dominant-baseline="middle"
					class="text-sm {isDark ? 'fill-gray-500' : 'fill-gray-400'}"
				>
					No data available
				</text>
			{/if}
		</svg>

		<!-- Legend -->
		{#if showLegend && pieData.length > 0}
			<div class="flex flex-col gap-2">
				{#each pieData as item}
					<div class="flex items-center gap-2">
						<div class="w-3 h-3 rounded-sm flex-shrink-0" style="background-color: {item.color}"></div>
						<span class="text-xs {isDark ? 'text-gray-400' : 'text-gray-600'} truncate max-w-[150px]">{item.name}</span>
						<span class="text-xs font-medium {isDark ? 'text-gray-300' : 'text-gray-700'}">{formatValue(item.value)}</span>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
