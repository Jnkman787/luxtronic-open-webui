<script lang="ts">
	/**
	 * Universal chart renderer component.
	 * Delegates to specific chart components based on chart type.
	 */
	import MultiSeriesLineChart from '$lib/components/admin/Dashboard/Charts/MultiSeriesLineChart.svelte';
	import BarChart from '$lib/components/admin/Dashboard/Charts/BarChart.svelte';
	import PieChart from '$lib/components/admin/Dashboard/Charts/PieChart.svelte';
	import ScatterChart from '$lib/components/admin/Dashboard/Charts/ScatterChart.svelte';

	export let chartData: {
		type: 'line' | 'bar' | 'pie' | 'scatter';
		title?: string;
		labels: string[];
		series: Array<{ name: string; values: number[]; color: string }>;
	};
	export let isDark: boolean = false;
	export let height: number = 250;
	export let showLegend: boolean = true;
	export let showGrid: boolean = true;

	$: chartType = chartData?.type || 'line';
	$: title = chartData?.title || '';
	$: labels = chartData?.labels || [];
	$: series = chartData?.series || [];
</script>

<div class="chart-renderer w-full">
	{#if chartType === 'line'}
		<MultiSeriesLineChart
			{title}
			{labels}
			{series}
			{isDark}
			{height}
			{showLegend}
			{showGrid}
		/>
	{:else if chartType === 'bar'}
		<BarChart
			{title}
			{labels}
			{series}
			{isDark}
			{height}
			{showLegend}
			{showGrid}
		/>
	{:else if chartType === 'pie'}
		<PieChart
			{title}
			{labels}
			{series}
			{isDark}
			{height}
			{showLegend}
		/>
	{:else if chartType === 'scatter'}
		<ScatterChart
			{title}
			{labels}
			{series}
			{isDark}
			{height}
			{showLegend}
			{showGrid}
		/>
	{:else}
		<div class="text-center py-8 text-sm {isDark ? 'text-gray-500' : 'text-gray-400'}">
			Unsupported chart type: {chartType}
		</div>
	{/if}
</div>
