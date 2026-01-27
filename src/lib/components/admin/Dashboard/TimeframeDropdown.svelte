<script lang="ts">
	/**
	 * Timeframe dropdown for selecting date range per chart.
	 */
	import { createEventDispatcher } from 'svelte';

	export let type: 'days' | 'hours' = 'days';
	export let value: number = 7;
	export let isDark: boolean = false;
	export let disabled: boolean = false;

	const dispatch = createEventDispatcher<{ change: { type: string; value: number } }>();

	const dayOptions = [1, 7, 14, 30];
	const hourOptions = [1, 6, 12, 24, 48];

	$: options = type === 'days' ? dayOptions : hourOptions;
	$: label = type === 'days' ? 'd' : 'h';

	function handleChange(event: Event) {
		const target = event.target as HTMLSelectElement;
		const newValue = parseInt(target.value, 10);
		value = newValue;
		dispatch('change', { type, value: newValue });
	}
</script>

<select
	{value}
	{disabled}
	on:change={handleChange}
	class="text-xs px-2 py-1 rounded border transition-colors
		{isDark
		? 'bg-gray-700 border-gray-600 text-gray-200 hover:border-gray-500'
		: 'bg-white border-gray-300 text-gray-700 hover:border-gray-400'}
		{disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
		focus:outline-none focus:ring-1 focus:ring-[#5CC9D3]"
>
	{#each options as opt}
		<option value={opt}>{opt}{label}</option>
	{/each}
</select>
