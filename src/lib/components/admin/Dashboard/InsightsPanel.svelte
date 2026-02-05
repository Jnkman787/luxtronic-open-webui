<script lang="ts">
	export type InsightItem = {
		title: string;
		description: string;
	};

	export let insights: InsightItem[] = [];
	export let isDark: boolean = false;
</script>

<div class="space-y-4">
	<h2 class="text-lg font-semibold {isDark ? 'text-white' : 'text-gray-900'}">Insights</h2>
	{#if !insights || insights.length === 0}
		<div class="p-6 rounded-lg border text-center {isDark ? 'bg-gray-800/50 border-gray-700/50 text-gray-400' : 'bg-white border-gray-200 text-gray-500'}">
			<p class="text-sm">No insights available for this dashboard yet.</p>
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
			{#each insights as insight}
				<div class="p-4 rounded-lg border {isDark ? 'bg-gray-800/50 border-gray-700/50' : 'bg-white border-gray-200'}">
					<h4 class="text-sm font-semibold {isDark ? 'text-white' : 'text-gray-900'}">
						{insight.title}
					</h4>
					<p class="text-xs mt-2 {isDark ? 'text-gray-400' : 'text-gray-600'}">
						{insight.description}
					</p>
				</div>
			{/each}
		</div>
	{/if}
</div>
