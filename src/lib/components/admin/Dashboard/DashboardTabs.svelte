<script lang="ts">
	/**
	 * Dashboard tabs component for switching between Quality Dashboard and My Stuff.
	 */
	export let tabs: Array<{ id: string; label: string }> = [];
	export let activeTab: string = '';
	export let isDark: boolean = false;

	function handleTabClick(tabId: string) {
		activeTab = tabId;
	}
</script>

{#if tabs.length > 1}
	<div class="flex border-b {isDark ? 'border-gray-700' : 'border-gray-200'} mb-4">
		{#each tabs as tab}
			<button
				class="px-4 py-2 font-medium text-sm transition-colors duration-150 -mb-px
					{activeTab === tab.id
					? `border-b-2 border-[#5CC9D3] ${isDark ? 'text-white' : 'text-gray-900'}`
					: `${isDark ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'}`}"
				on:click={() => handleTabClick(tab.id)}
			>
				{tab.label}
			</button>
		{/each}
	</div>
{/if}
