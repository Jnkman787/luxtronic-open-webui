<script lang="ts">
	import type { FinalCheckIncident } from '$lib/apis/dashboard';

	export let incidents: FinalCheckIncident[] = [];
	export let isDark: boolean = false;
	export let loading: boolean = false;
	export let error: string | null = null;

	let selectedImage: string | null = null;

	const classLabels: Record<string, string> = {
		bad: 'Bad Slipsheet'
	};
	const canpackPriority = ['object', 'pattern_disruption', 'missing'];

	function formatTime(timeStr: string): string {
		const date = new Date(timeStr);
		return date.toLocaleString(undefined, {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function formatClassName(name: string | null | undefined): string {
		if (!name) return 'Unknown';
		return classLabels[name.toLowerCase()] || name;
	}

	function openImage(url: string) {
		selectedImage = url;
	}

	function closeImage() {
		selectedImage = null;
	}

	function handleImageError(event: Event, incident: FinalCheckIncident) {
		const target = event.currentTarget as HTMLImageElement | null;
		if (!target || !incident.image_url_png) return;
		if (target.src !== incident.image_url_png) {
			target.src = incident.image_url_png;
		}
	}
	function getTimeValue(incident: FinalCheckIncident) {
		const value = Date.parse(incident.time || '');
		return Number.isNaN(value) ? 0 : value;
	}
	function getPriority(incident: FinalCheckIncident) {
		const name = (incident.class_name || '').toLowerCase();
		const index = canpackPriority.indexOf(name);
		return index === -1 ? canpackPriority.length : index;
	}
	$: slipsheetIncidents = incidents.filter(
		(incident) => (incident.cell || '').toLowerCase() === 'slipsheet'
	);
	$: badIncidents = slipsheetIncidents
		.filter((incident) => (incident.class_name || '').toLowerCase() === 'bad')
		.sort((a, b) => getTimeValue(b) - getTimeValue(a))
		.slice(0, 20);
	$: canpackRaw = slipsheetIncidents.filter(
		(incident) => (incident.class_name || '').toLowerCase() !== 'bad'
	);
	$: canpackRecent = [...canpackRaw]
		.sort((a, b) => getTimeValue(b) - getTimeValue(a))
		.slice(0, 20);
	$: canpackIncidents = [...canpackRecent].sort((a, b) => {
		const priorityDiff = getPriority(a) - getPriority(b);
		if (priorityDiff !== 0) return priorityDiff;
		return getTimeValue(b) - getTimeValue(a);
	});
	$: sections = [
		{ id: 'bad', title: 'Bad Slipsheet', items: badIncidents },
		{ id: 'canpack', title: 'Canpack', items: canpackIncidents }
	];
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
	{:else if slipsheetIncidents.length === 0}
		<div class="p-8 text-center {isDark ? 'text-gray-400' : 'text-gray-500'}">
			<p class="text-sm">No slipsheet or canpack incidents found for the selected period</p>
		</div>
	{:else}
		<div class="space-y-6">
			{#each sections as section}
				<div class="space-y-2">
					<div class="flex items-center justify-between">
						<h4 class="text-sm font-semibold {isDark ? 'text-white' : 'text-gray-900'}">
							{section.title}
						</h4>
						<span class="text-xs {isDark ? 'text-gray-400' : 'text-gray-500'}">
							{section.items.length} incidents
						</span>
					</div>
					{#if section.items.length === 0}
						<div class="p-4 rounded-lg border text-center {isDark ? 'bg-gray-800/50 border-gray-700/50 text-gray-400' : 'bg-white border-gray-200 text-gray-500'}">
							<p class="text-sm">No incidents in this category</p>
						</div>
					{:else}
						<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
							{#each section.items as incident}
								<div
									class="rounded-lg border overflow-hidden {isDark
										? 'bg-gray-800/50 border-gray-700/50'
										: 'bg-white border-gray-200'}"
								>
									<div class="px-2 py-1 text-xs font-medium {isDark ? 'bg-gray-700 text-gray-200' : 'bg-gray-100 text-gray-700'}">
										{formatClassName(incident.class_name)}
									</div>
									{#if incident.image_url}
										<button
											class="w-full aspect-video bg-gray-900 relative overflow-hidden cursor-pointer hover:opacity-90 transition-opacity"
											on:click={() => openImage(incident.image_url || '')}
										>
											<img
												src={incident.image_url}
												alt="Incident {incident.id}"
												class="w-full h-full object-cover"
												loading="lazy"
												on:error={(e) => handleImageError(e, incident)}
											/>
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
												{incident.line || 'CX'}
											</span>
										</div>
										<p class="text-xs {isDark ? 'text-gray-300' : 'text-gray-700'}">
											Class: {formatClassName(incident.class_name)}
										</p>
										<p class="text-xs {isDark ? 'text-gray-500' : 'text-gray-400'}">
											Score: {incident.anomaly_score ?? 0} | Conf: {incident.confidence ?? 0}
										</p>
									</div>
								</div>
							{/each}
						</div>
					{/if}
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
		<div class="max-w-5xl max-h-[90vh] p-2">
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
