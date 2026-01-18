<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';

	import { user } from '$lib/stores';
import { updateUserProfile, getSessionUser } from '$lib/apis/auths';
import { changeLanguage } from '$lib/i18n';
import { getTenantById } from '$lib/apis/tenants';
	import { generateInitialsImage } from '$lib/utils';
	import Textarea from '$lib/components/common/Textarea.svelte';
	import UserProfileImage from './Account/UserProfileImage.svelte';

	const i18n = getContext('i18n');

	export let saveHandler: Function;

let profileImageUrl = '';
let name = '';
let jobTitle = '';
let primaryLocation = '';
let phoneNumber = '';
let jobDescription = '';
let tenantLogoUrl = '';
	let defaultLanguage = 'en-US';
	const defaultWorkDayIndices = [1, 2, 3, 4, 5];
	const defaultWorkHoursStart = '09:00';
	const defaultWorkHoursEnd = '17:00';
	const workDays = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
	let selectedWorkDays = new Set<number>(defaultWorkDayIndices);
	let isAlwaysAvailable = false;
	let workHoursStart = defaultWorkHoursStart;
	let workHoursEnd = defaultWorkHoursEnd;

	const normalizeLanguage = (value: string) => (value === 'en-ES' ? 'es-ES' : value);
	const toggleWorkDay = (index: number) => {
		if (isAlwaysAvailable) {
			isAlwaysAvailable = false;
		}
		const next = new Set(selectedWorkDays);
		if (next.has(index)) {
			next.delete(index);
		} else {
			next.add(index);
		}
		selectedWorkDays = next;
	};
	const setAllWorkDays = () => {
		selectedWorkDays = new Set(workDays.map((_, index) => index));
	};
	const handleWorkHoursChange = (value: string, field: 'start' | 'end') => {
		if (isAlwaysAvailable) {
			isAlwaysAvailable = false;
		}
		if (field === 'start') {
			workHoursStart = value;
		} else {
			workHoursEnd = value;
		}
	};
	const parseWorkDays = (value: string | null | undefined) => {
		if (!value) {
			return new Set<number>();
		}
		const indices = value
			.split(',')
			.map((item) => Number(item))
			.filter((item) => Number.isInteger(item) && item >= 0 && item < workDays.length);
		return new Set<number>(indices);
	};
	const serializeWorkDays = () => {
		if (!selectedWorkDays.size) {
			return null;
		}
		return [...selectedWorkDays].sort((a, b) => a - b).join(',');
	};
	const resolveWorkDays = (value: string | null | undefined) =>
		value ? parseWorkDays(value) : new Set<number>(defaultWorkDayIndices);
	const applySessionUserFields = (sessionUser: typeof $user | null) => {
		if (!sessionUser) {
			name = '';
			profileImageUrl = '';
			jobTitle = '';
			primaryLocation = '';
			phoneNumber = '';
			selectedWorkDays = new Set<number>(defaultWorkDayIndices);
			workHoursStart = defaultWorkHoursStart;
			workHoursEnd = defaultWorkHoursEnd;
			jobDescription = '';
			tenantLogoUrl = '';
			defaultLanguage = normalizeLanguage(defaultLanguage);
			isAlwaysAvailable = false;
			return;
		}

		name = sessionUser?.name ?? '';
		profileImageUrl = sessionUser?.profile_image_url ?? '';
		jobTitle = sessionUser?.job_title ?? '';
		primaryLocation = sessionUser?.primary_location ?? '';
		phoneNumber = sessionUser?.phone_number ?? '';
		selectedWorkDays = resolveWorkDays(sessionUser?.work_days);
		workHoursStart = sessionUser?.work_hours_start ?? defaultWorkHoursStart;
		workHoursEnd = sessionUser?.work_hours_end ?? defaultWorkHoursEnd;
		jobDescription = sessionUser?.job_description ?? '';
		tenantLogoUrl = sessionUser?.tenant_logo_image_url ?? '';
		defaultLanguage = normalizeLanguage(sessionUser?.default_language ?? defaultLanguage);
		isAlwaysAvailable =
			selectedWorkDays.size === workDays.length &&
			workHoursStart === '00:00' &&
			workHoursEnd === '23:59';
	};

	const submitHandler = async () => {
		if (name !== $user?.name) {
			if (profileImageUrl === generateInitialsImage($user?.name) || profileImageUrl === '') {
				profileImageUrl = generateInitialsImage(name);
			}
		}

			const normalizedLanguage = normalizeLanguage(defaultLanguage);
			const serializedWorkDays = serializeWorkDays();
			const updatedUser = await updateUserProfile(localStorage.token, {
				name: name,
				profile_image_url: profileImageUrl,
				job_title: jobTitle ? jobTitle : null,
				primary_location: primaryLocation ? primaryLocation : null,
				phone_number: phoneNumber ? phoneNumber : null,
				work_days: serializedWorkDays,
				work_hours_start: workHoursStart ? workHoursStart : null,
				work_hours_end: workHoursEnd ? workHoursEnd : null,
				job_description: jobDescription ? jobDescription : null,
				default_language: normalizedLanguage
			}).catch((error) => {
				toast.error(`${error}`);
			});

		if (updatedUser) {
			const sessionUser = await getSessionUser(localStorage.token).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			await user.set(sessionUser);
				applySessionUserFields(sessionUser);
				changeLanguage(normalizedLanguage);
				return true;
			}
			return false;
		};

	onMount(async () => {
		const sessionUser = await getSessionUser(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

			if (sessionUser) {
				applySessionUserFields(sessionUser);

				if (!tenantLogoUrl && sessionUser?.tenant_id) {
					const tenant = await getTenantById(localStorage.token, sessionUser.tenant_id).catch(
						(error) => {
							console.error(error);
							return null;
						}
					);
					if (tenant?.logo_image_url) {
						tenantLogoUrl = tenant.logo_image_url;
					}
				}
			} else {
				applySessionUserFields(null);
			}
		});
</script>

<div id="tab-account" class="flex flex-col h-full justify-between text-sm">
	<div class=" overflow-y-scroll max-h-[28rem] md:max-h-full">
		<div class="space-y-1">
			<div>
				<div class="text-base font-medium">{$i18n.t('Your Account')}</div>

				<div class="text-xs text-gray-500 mt-0.5">
					{$i18n.t('Manage your account information.')}
				</div>
			</div>

			<!-- <div class=" text-sm font-medium">{$i18n.t('Account')}</div> -->

			<div class="flex space-x-5 my-4">
				<div class="flex flex-col items-center gap-3">
					<UserProfileImage bind:profileImageUrl user={$user} />
					{#if tenantLogoUrl}
						<div class="flex flex-col items-center space-y-1">
							<div class="max-h-16 max-w-[10rem] rounded-xl border border-gray-100 bg-white px-3 py-2 dark:border-gray-800 dark:bg-gray-900">
								<img
									src={tenantLogoUrl}
									alt={$i18n.t('Tenant Logo')}
									class="max-h-12 w-auto object-contain"
								/>
							</div>
						</div>
					{/if}
				</div>

				<div class="flex flex-1 flex-col">
					<div class=" flex-1 w-full">
								<div class="flex flex-col w-full">
									<div class=" mb-1 text-xs font-medium">{$i18n.t('Name')}</div>

							<div class="flex-1">
								<input
									class="w-full text-sm dark:text-gray-300 bg-transparent outline-hidden"
									type="text"
									bind:value={name}
									required
									placeholder={$i18n.t('Enter your name')}
								/>
								</div>

								<div class="flex flex-col w-full mt-2">
									<div class=" mb-1 text-xs font-medium">{$i18n.t('Default Language')}</div>

									<div class="flex-1">
										<select
											class="w-full text-sm dark:text-gray-300 bg-transparent outline-hidden"
											bind:value={defaultLanguage}
										>
											<option value="en-US">English (en-US)</option>
											<option value="es-ES">Spanish (es-ES)</option>
										</select>
									</div>
								</div>
						</div>

						<div class="flex flex-col w-full mt-2">
							<div class=" mb-1 text-xs font-medium">{$i18n.t('Phone Number')}</div>

							<div class="flex-1">
								<input
									class="w-full text-sm dark:text-gray-300 bg-transparent outline-hidden"
									type="tel"
									inputmode="tel"
									pattern="\\+?[0-9\\s\\-()]*"
									bind:value={phoneNumber}
									maxlength={25}
									placeholder={$i18n.t('Enter your phone number')}
									on:input={(event) => {
										const rawValue = event.currentTarget.value;
										const hasLeadingPlus = rawValue.startsWith('+');
										const allowedChars = rawValue.replace(/[^0-9()\-\s+]/g, '');
										const noExtraPluses = allowedChars.replace(/\+/g, '');
										phoneNumber = `${hasLeadingPlus ? '+' : ''}${noExtraPluses}`;
									}}
								/>
							</div>
						</div>

						<div class="flex flex-col w-full mt-2">
							<div class=" mb-1 text-xs font-medium">{$i18n.t('Title')}</div>

							<div class="flex-1">
								<input
									class="w-full text-sm dark:text-gray-300 bg-transparent outline-hidden"
									type="text"
									bind:value={jobTitle}
									maxlength={255}
									placeholder={$i18n.t('Enter your title')}
								/>
							</div>
						</div>

						<div class="flex flex-col w-full mt-2">
							<div class=" mb-1 text-xs font-medium">{$i18n.t('Primary Location')}</div>

							<div class="flex-1">
								<input
									class="w-full text-sm dark:text-gray-300 bg-transparent outline-hidden"
									type="text"
									bind:value={primaryLocation}
									maxlength={255}
									placeholder={$i18n.t('Enter your primary location')}
								/>
							</div>
						</div>

						<div class="flex flex-col w-full mt-2">
							<div class=" mb-1 text-xs font-medium">{$i18n.t('Job Description')}</div>

							<div class="flex-1">
								<Textarea
									className="w-full text-sm dark:text-gray-300 bg-transparent outline-hidden"
									minSize={60}
									maxlength={2500}
									bind:value={jobDescription}
									placeholder={$i18n.t('Describe your role and responsibilities')}
								/>
							</div>
						</div>

						<div class="flex flex-col w-full mt-2">
							<div class=" mb-1 text-xs font-medium">Work Hours (Availability)</div>

							<div class="flex flex-wrap gap-2">
								{#each workDays as day, index}
									<button
										type="button"
										class={`h-8 w-8 rounded-full text-xs font-semibold transition ${
											selectedWorkDays.has(index)
												? 'bg-black text-white'
												: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-300'
										}`}
										aria-pressed={selectedWorkDays.has(index)}
										on:click={() => toggleWorkDay(index)}
									>
										{day}
									</button>
								{/each}
							</div>

							<div class="mt-3 flex items-center gap-3">
								<input
									class="w-32 text-sm dark:text-gray-300 bg-transparent outline-hidden"
									type="time"
									aria-label="Work hours start"
									bind:value={workHoursStart}
									on:input={(event) =>
										handleWorkHoursChange(event.currentTarget.value, 'start')}
								/>
								<span class="text-xs text-gray-500">to</span>
								<input
									class="w-32 text-sm dark:text-gray-300 bg-transparent outline-hidden"
									type="time"
									aria-label="Work hours end"
									bind:value={workHoursEnd}
									on:input={(event) =>
										handleWorkHoursChange(event.currentTarget.value, 'end')}
								/>
								<button
									type="button"
									class="flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold transition"
									aria-pressed={isAlwaysAvailable}
									on:click={() => {
										isAlwaysAvailable = !isAlwaysAvailable;
										if (isAlwaysAvailable) {
											setAllWorkDays();
											workHoursStart = '00:00';
											workHoursEnd = '23:59';
										}
									}}
								>
									<span
										class={`flex h-5 w-5 items-center justify-center rounded border ${
											isAlwaysAvailable
												? 'border-black bg-black text-white'
												: 'border-gray-300 bg-white text-gray-400 dark:border-gray-600 dark:bg-gray-900'
										}`}
										aria-hidden="true"
									>
										{#if isAlwaysAvailable}
											<svg
												class="h-3.5 w-3.5"
												viewBox="0 0 12 10"
												fill="none"
												xmlns="http://www.w3.org/2000/svg"
											>
												<path
													d="M1 5L4.5 8.5L11 1.5"
													stroke="currentColor"
													stroke-width="1.5"
													stroke-linecap="round"
													stroke-linejoin="round"
												/>
											</svg>
										{/if}
									</span>
									<span class={isAlwaysAvailable ? 'text-black' : 'text-gray-500 dark:text-gray-300'}>
										24/7
									</span>
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

	</div>

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
			on:click={async () => {
				const res = await submitHandler();

				if (res) {
					saveHandler();
				}
			}}
		>
			{$i18n.t('Save')}
		</button>
	</div>
</div>
