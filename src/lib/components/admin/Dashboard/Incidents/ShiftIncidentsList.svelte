<script lang="ts">
	import type { Incident } from '$lib/apis/dashboard';

	export let incidents: Incident[] = [];
	export let isDark: boolean = false;
	export let loading: boolean = false;
	export let error: string | null = null;

	let selectedImage: string | null = null;

	function formatTime(timeStr: string): string {
		const date = new Date(timeStr);
		return date.toLocaleString(undefined, {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function formatSummary(incident: Incident): string {
		const down = incident.down ?? 0;
		const can = incident.can ?? 0;
		return `Down: ${down} | Can: ${can}`;
	}

	function formatConfidence(incident: Incident): string {
		const downConf = incident.down_conf ?? 0;
		const canConf = incident.can_conf ?? 0;
		const parts = [];
		if (downConf > 0) parts.push(`Down: ${(downConf * 100).toFixed(0)}%`);
		if (canConf > 0) parts.push(`Can: ${(canConf * 100).toFixed(0)}%`);
		return parts.join(' | ');
	}

	function openImage(url: string) {
		selectedImage = url;
	}

	function closeImage() {
		selectedImage = null;
	}
</script>

<div class="space-y-3">
	{#if loading}
		<div class="flex items-center justify-center h-32">
			<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#5CC9D3]"></div>
		</div>
	{:else if error}
		<div class="p-3 rounded-lg {isDark ? 'bg-red-900/50 text-red-200' : 'bg-red-50 text-red-700'}">
			{error}
		</div>
	{:else if incidents.length === 0}
		<div class="p-8 text-center {isDark ? 'text-gray-400' : 'text-gray-500'}">
			<p class="text-sm">No incidents found for the selected period</p>
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
			{#each incidents as incident}
				<div
					class="rounded-lg border overflow-hidden {isDark
						? 'bg-gray-800/50 border-gray-700/50'
						: 'bg-white border-gray-200'}"
				>
					{#if incident.image_url}
						<button
							class="w-full aspect-video bg-gray-900 relative overflow-hidden cursor-pointer hover:opacity-90 transition-opacity"
							on:click={() => openImage(incident.image_url || '')}
						>
							<img
								src={incident.image_url}
								alt="Incident {incident.uuid}"
								class="w-full h-full object-cover"
								loading="lazy"
							/>
							<div class="absolute bottom-1 right-1 px-1.5 py-0.5 rounded text-xs bg-black/70 text-white">
								{incident.inc_hits} hits
							</div>
						</button>
					{:else}
						<div class="w-full aspect-video bg-gray-800 flex items-center justify-center">
							<span class="text-xs {isDark ? 'text-gray-500' : 'text-gray-400'}">No image</span>
						</div>
					{/if}

					<div class="p-2 space-y-1">
						<div class="flex items-center justify-between">
							<span class="text-xs font-medium {isDark ? 'text-white' : 'text-gray-900'}">
								{formatTime(incident.time)}
							</span>
							<span class="text-xs px-1.5 py-0.5 rounded {isDark ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600'}">
								{incident.system}
							</span>
						</div>
						<p class="text-xs {isDark ? 'text-gray-300' : 'text-gray-700'}">
							{formatSummary(incident)}
						</p>
						{#if formatConfidence(incident)}
							<p class="text-xs {isDark ? 'text-gray-500' : 'text-gray-400'}">
								Conf: {formatConfidence(incident)}
							</p>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

{#if selectedImage}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
		on:click={closeImage}
		on:keydown={(e) => e.key === 'Escape' && closeImage()}
		role="button"
		tabindex="0"
	>
		<div class="max-w-4xl max-h-[90vh] p-2">
			<img
				src={selectedImage}
				alt="Incident detail"
				class="max-w-full max-h-[85vh] object-contain rounded-lg"
			/>
			<button
				class="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white"
				on:click|stopPropagation={closeImage}
			>
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>
	</div>
{/if}
