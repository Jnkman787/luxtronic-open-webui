<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';

	import DashboardTabs from '$lib/components/admin/Dashboard/DashboardTabs.svelte';
	import TenantDashboard from '$lib/components/admin/Dashboard/TenantDashboard.svelte';
	import MyStuffDashboard from '$lib/components/admin/Dashboard/MyStuffDashboard.svelte';

	import { getAvailableDashboards } from '$lib/apis/dashboard';
	import { getSavedItems } from '$lib/apis/saved-items';

	const i18n = getContext('i18n');

	let loaded = false;
	let token = '';
	let isDark = false;

	// Tab state
	let tabs: Array<{ id: string; label: string }> = [];
	let activeTab = 'my-stuff';
	let hasQualityDashboard = false;
	let hasSavedItems = false;

	onMount(async () => {
		token = localStorage.getItem('token') || '';

		if (!token) {
			await goto('/auth');
			return;
		}

		// Detect dark mode
		isDark = document.documentElement.classList.contains('dark');

		// Check what dashboards are available in parallel
		try {
			const [tenants, savedItems] = await Promise.all([
				getAvailableDashboards(token).catch(() => []),
				getSavedItems(token).catch(() => [])
			]);

			hasQualityDashboard = tenants.length > 0;
			hasSavedItems = savedItems.length > 0;

			// Build tabs list - Quality Dashboard first if available, then My Stuff
			tabs = [];
			if (hasQualityDashboard) {
				tabs.push({ id: 'quality', label: 'Quality Dashboard' });
			}
			tabs.push({ id: 'my-stuff', label: 'My Stuff' });

			// Default to Quality Dashboard if available, otherwise My Stuff
			if (hasQualityDashboard) {
				activeTab = 'quality';
			} else {
				activeTab = 'my-stuff';
			}
		} catch (e) {
			console.error('Failed to check available dashboards:', e);
			// Default to My Stuff if check fails
			tabs = [{ id: 'my-stuff', label: 'My Stuff' }];
			activeTab = 'my-stuff';
		}

		loaded = true;
	});
</script>

<svelte:head>
	<title>{activeTab === 'quality' ? $i18n.t('Quality Dashboard') : $i18n.t('My Stuff')}</title>
</svelte:head>

{#if loaded}
	<div class="w-full h-full">
		<!-- Tabs (only shown if there are multiple tabs) -->
		{#if tabs.length > 1}
			<div class="px-4 pt-4">
				<DashboardTabs {tabs} bind:activeTab {isDark} />
			</div>
		{/if}

		<!-- Tab content -->
		{#if activeTab === 'quality' && hasQualityDashboard}
			<TenantDashboard {token} />
		{:else if activeTab === 'my-stuff'}
			<MyStuffDashboard {token} {isDark} />
		{/if}
	</div>
{:else}
	<div class="flex items-center justify-center h-full">
		<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#5CC9D3]"></div>
	</div>
{/if}
