<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';

	import { user } from '$lib/stores';
	import { updateUserProfile, getSessionUser } from '$lib/apis/auths';
	import { changeLanguage } from '$lib/i18n';
	import { getTenantById } from '$lib/apis/tenants';
	import { generateInitialsImage } from '$lib/utils';
	import Textarea from '$lib/components/common/Textarea.svelte';
	import phoneCountryCodeOptions from '$lib/phone-country-codes.json';
	import { AsYouType, getCountryCallingCode, parsePhoneNumberFromString } from 'libphonenumber-js';
	import type { CountryCode } from 'libphonenumber-js';
	import UserProfileImage from './Account/UserProfileImage.svelte';

	const i18n = getContext('i18n');

	export let saveHandler: Function;

	let profileImageUrl = '';
	let name = '';
	let jobTitle = '';
	let primaryLocation = '';
	let phoneNumber = '';
	let phoneCountryCode = '+1';
	let phoneNumberError = '';
	let jobDescription = '';
	let tenantLogoUrl = '';
	let defaultLanguage = 'en-US';
	const defaultWorkDayIndices = [1, 2, 3, 4, 5];
	const defaultWorkHoursStart = '09:00';
	const defaultWorkHoursEnd = '17:00';
	const workDays = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
	const phoneCountryCodes = (phoneCountryCodeOptions as Array<{ name: string; iso2: string }>)
		.map((option) => {
			try {
				return {
					name: option.name,
					iso2: option.iso2,
					code: `+${getCountryCallingCode(option.iso2 as CountryCode)}`
				};
			} catch (error) {
				console.error('Invalid country code entry', option, error);
				return null;
			}
		})
		.filter((option): option is { name: string; iso2: string; code: string } => option !== null)
		.sort((a, b) => a.name.localeCompare(b.name));
	const prioritizedPhoneCountryCodes = [
		...phoneCountryCodes.filter((option) => option.iso2 === 'US'),
		...phoneCountryCodes.filter((option) => option.iso2 !== 'US')
	];
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
	const phoneCountryCodeDigits = (value: string) => value.replace(/\D/g, '');
	const phoneCountryCodeDigitsList = phoneCountryCodes
		.map((option) => phoneCountryCodeDigits(option.code))
		.sort((a, b) => b.length - a.length);
	const MAX_E164_DIGITS = 15;
	const resolveCountryIso2 = (countryCode: string) =>
		phoneCountryCodes.find((option) => option.code === countryCode)?.iso2?.toUpperCase() ??
		undefined;
	const phoneTemplateCache = new Map<
		string,
		{ template: string; maxDigits: number; positions: number[] }
	>();
	let suppressPhoneInputCaret = false;
	const buildTemplateForSeed = (seedDigit: string, iso2?: string) => {
		const typer = new AsYouType(iso2 as CountryCode | undefined);
		let lastTemplate = typer.getTemplate() || '';
		for (let index = 0; index < MAX_E164_DIGITS; index += 1) {
			typer.input(seedDigit);
			const nextTemplate = typer.getTemplate();
			if (nextTemplate) {
				lastTemplate = nextTemplate;
			}
		}
		const maxDigits = (lastTemplate.match(/x/g) ?? []).length;
		const positions = lastTemplate
			? [...lastTemplate]
					.map((char, index) => (char === 'x' ? index : null))
					.filter((index): index is number => index !== null)
			: [];
		return { template: lastTemplate, maxDigits, positions };
	};
	const resolvePhoneTemplate = (countryCode: string) => {
		const cacheKey = countryCode;
		const cached = phoneTemplateCache.get(cacheKey);
		if (cached) {
			return cached;
		}
		const isNanp = phoneCountryCodeDigits(countryCode) === '1';
		if (isNanp) {
			const template = '(xxx) xxx-xxxx';
			const positions = [...template]
				.map((char, index) => (char === 'x' ? index : null))
				.filter((index): index is number => index !== null);
			const templateData = { template, maxDigits: 10, positions };
			phoneTemplateCache.set(cacheKey, templateData);
			return templateData;
		}
		const iso2 = resolveCountryIso2(countryCode);
		let bestTemplate = { template: '', maxDigits: 0, positions: [] as number[] };
		['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'].forEach((seedDigit) => {
			const candidate = buildTemplateForSeed(seedDigit, iso2);
			if (
				candidate.maxDigits > bestTemplate.maxDigits ||
				(candidate.maxDigits === bestTemplate.maxDigits &&
					candidate.template.length > bestTemplate.template.length)
			) {
				bestTemplate = candidate;
			}
		});
		const templateData = {
			template: bestTemplate.template,
			maxDigits: bestTemplate.maxDigits || MAX_E164_DIGITS,
			positions: bestTemplate.positions
		};
		phoneTemplateCache.set(cacheKey, templateData);
		return templateData;
	};
	const buildPhoneMaskData = (digits: string, countryCode: string) => {
		const normalized = digits.replace(/\D/g, '').slice(0, MAX_E164_DIGITS);
		const templateData = resolvePhoneTemplate(countryCode);
		const template = templateData.template;

		if (!template) {
			const fallback = normalized;
			const positions = [...fallback]
				.map((char, index) => (/\d/.test(char) ? index : null))
				.filter((index): index is number => index !== null);
			return {
				masked: fallback,
				positions,
				maxDigits: MAX_E164_DIGITS,
				digits: normalized
			};
		}

		const maxDigits = templateData.maxDigits || MAX_E164_DIGITS;
		const trimmed = normalized.slice(0, maxDigits);
		let masked = '';
		let digitIndex = 0;
		for (let index = 0; index < template.length; index += 1) {
			const char = template[index];
			if (char === 'x') {
				masked += digitIndex < trimmed.length ? trimmed[digitIndex] : '_';
				digitIndex += 1;
			} else {
				masked += char;
			}
		}
		const positions = [...masked]
			.map((char, index) => (char === '_' || /\d/.test(char) ? index : null))
			.filter((index): index is number => index !== null);
		return {
			masked,
			positions,
			maxDigits,
			digits: trimmed
		};
	};
	const formatPhoneInputValue = (digits: string, countryCode: string) =>
		buildPhoneMaskData(digits, countryCode).masked;
	const positionPhoneCaret = (target: HTMLInputElement, formatted: string) => {
		const nextBlank = formatted.indexOf('_');
		const caret = nextBlank === -1 ? formatted.length : nextBlank;
		target.setSelectionRange(caret, caret);
		requestAnimationFrame(() => {
			target.setSelectionRange(caret, caret);
		});
	};
	const positionPhoneCaretByDigits = (
		target: HTMLInputElement,
		maskData: { masked: string; positions: number[] },
		digitsLength: number
	) => {
		if (!maskData.positions.length) {
			positionPhoneCaret(target, maskData.masked);
			return;
		}
		const index = Math.min(digitsLength, maskData.positions.length);
		let caret: number;
		if (index >= maskData.positions.length) {
			const nextBlank = maskData.masked.indexOf('_');
			caret = nextBlank === -1 ? maskData.masked.length : nextBlank;
		} else {
			caret = maskData.positions[index];
		}
		target.setSelectionRange(caret, caret);
		requestAnimationFrame(() => {
			target.setSelectionRange(caret, caret);
		});
	};
	const handlePhoneInput = (event: Event) => {
		const target = event.currentTarget as HTMLInputElement;
		const rawDigits = target.value.replace(/\D/g, '');
		const maskData = buildPhoneMaskData(rawDigits, phoneCountryCode);
		phoneNumber = maskData.digits;
		target.value = maskData.masked;
		if (suppressPhoneInputCaret) {
			suppressPhoneInputCaret = false;
			return;
		}
		positionPhoneCaretByDigits(target, maskData, maskData.digits.length);
	};
	const handlePhoneKeydown = (event: KeyboardEvent) => {
		if (event.key !== 'Backspace' && event.key !== 'Delete') {
			return;
		}
		const target = event.currentTarget as HTMLInputElement;
		if (!phoneNumber.length) {
			event.preventDefault();
			const { masked, positions } = buildPhoneMaskData(phoneNumber, phoneCountryCode);
			target.value = masked;
			const caret = positions[0] ?? 0;
			requestAnimationFrame(() => {
				target.setSelectionRange(caret, caret);
			});
			return;
		}
		const selectionStart = target.selectionStart ?? 0;
		const selectionEnd = target.selectionEnd ?? 0;
		const isSelection = selectionStart !== selectionEnd;
		const removeIndices: number[] = [];
		const { positions } = buildPhoneMaskData(phoneNumber, phoneCountryCode);
		if (!positions.length) {
			return;
		}

		if (isSelection) {
			positions.forEach((pos, index) => {
				if (pos >= selectionStart && pos < selectionEnd) {
					removeIndices.push(index);
				}
			});
		} else if (event.key === 'Backspace') {
			const prevPos = [...positions].filter((pos) => pos < selectionStart).pop();
			if (prevPos !== undefined) {
				removeIndices.push(positions.indexOf(prevPos));
			}
		} else {
			const nextPos = positions.find((pos) => pos >= selectionStart);
			if (nextPos !== undefined) {
				removeIndices.push(positions.indexOf(nextPos));
			}
		}

		if (!removeIndices.length) {
			return;
		}
		event.preventDefault();
		suppressPhoneInputCaret = true;
		phoneNumber = phoneNumber
			.split('')
			.filter((_, index) => !removeIndices.includes(index))
			.join('');
		const nextMaskData = buildPhoneMaskData(phoneNumber, phoneCountryCode);
		target.value = nextMaskData.masked;

		let caret = nextMaskData.positions[0] ?? 0;
		if (isSelection) {
			caret =
				nextMaskData.positions.find((pos) => pos >= selectionStart) ??
				nextMaskData.masked.length;
		} else if (event.key === 'Backspace') {
			caret = [...nextMaskData.positions].filter((pos) => pos < selectionStart).pop() ?? caret;
		} else {
			caret =
				nextMaskData.positions.find((pos) => pos >= selectionStart) ??
				nextMaskData.masked.length;
		}
		requestAnimationFrame(() => {
			target.setSelectionRange(caret, caret);
		});
	};
	const parsePhoneE164 = (value: string | null | undefined) => {
		if (!value) {
			return { countryCode: phoneCountryCode, nationalNumber: '' };
		}
		const parsed = parsePhoneNumberFromString(value);
		if (parsed?.countryCallingCode) {
			return {
				countryCode: `+${parsed.countryCallingCode}`,
				nationalNumber: parsed.nationalNumber
			};
		}
		const digits = value.replace(/\D/g, '');
		if (!digits) {
			return { countryCode: phoneCountryCode, nationalNumber: '' };
		}
		const matchedCode = phoneCountryCodeDigitsList.find((code) => digits.startsWith(code));
		if (matchedCode) {
			return {
				countryCode: `+${matchedCode}`,
				nationalNumber: digits.slice(matchedCode.length)
			};
		}
		return { countryCode: phoneCountryCode, nationalNumber: digits };
	};
	const buildPhoneE164 = (countryCode: string, number: string) => {
		const codeDigits = phoneCountryCodeDigits(countryCode);
		const numberDigits = number.replace(/\D/g, '');
		if (!codeDigits || !numberDigits) {
			return null;
		}
		return `+${codeDigits}${numberDigits}`;
	};
	const isValidPhoneNumber = (countryCode: string, number: string) => {
		const e164 = buildPhoneE164(countryCode, number);
		if (!e164) {
			return false;
		}
		const parsed = parsePhoneNumberFromString(e164);
		if (!parsed || !parsed.isValid()) {
			return false;
		}
		const selectedCodeDigits = phoneCountryCodeDigits(countryCode);
		return parsed.countryCallingCode === selectedCodeDigits;
	};
	const resetPhoneNumberError = () => {
		phoneNumberError = '';
	};
	const handlePhoneFocus = (event: Event) => {
		resetPhoneNumberError();
		const target = event.currentTarget as HTMLInputElement;
		const { masked } = buildPhoneMaskData(phoneNumber, phoneCountryCode);
		target.value = masked;
		positionPhoneCaret(target, masked);
	};
	const applySessionUserFields = (sessionUser: typeof $user | null) => {
		if (!sessionUser) {
			name = '';
			profileImageUrl = '';
			jobTitle = '';
			primaryLocation = '';
			phoneNumber = '';
			phoneCountryCode = '+1';
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
		const parsedPhone = parsePhoneE164(sessionUser?.phone_number);
		phoneNumber = parsedPhone.nationalNumber;
		phoneCountryCode = parsedPhone.countryCode;
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
			const combinedPhoneNumber = buildPhoneE164(phoneCountryCode, phoneNumber);
			if (phoneNumber && !isValidPhoneNumber(phoneCountryCode, phoneNumber)) {
				phoneNumberError = $i18n.t('Invalid phone number');
				return false;
			}
			const updatedUser = await updateUserProfile(localStorage.token, {
				name: name,
				profile_image_url: profileImageUrl,
				job_title: jobTitle ? jobTitle : null,
				primary_location: primaryLocation ? primaryLocation : null,
				phone_number: combinedPhoneNumber,
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

							<div class="flex w-full gap-2">
								<div
									class="relative w-20 rounded-xl bg-gray-100 pl-3 pr-6 text-sm text-gray-900 dark:bg-gray-800 dark:text-gray-300"
								>
									<span class="flex h-9 items-center">{phoneCountryCode}</span>
									<svg
										class="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500 dark:text-gray-300"
										viewBox="0 0 20 20"
										fill="currentColor"
										aria-hidden="true"
									>
										<path
											fill-rule="evenodd"
											d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.24a.75.75 0 01-1.06 0L5.21 8.29a.75.75 0 01.02-1.08z"
											clip-rule="evenodd"
										/>
									</svg>
									<select
										class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
										bind:value={phoneCountryCode}
										aria-label={$i18n.t('Country Code')}
										on:change={resetPhoneNumberError}
									>
									{#each prioritizedPhoneCountryCodes as option}
										<option value={option.code}>
											{option.name} ({option.code})
										</option>
									{/each}
									</select>
								</div>

								<div class="flex-1">
									<input
										class={`w-full text-sm dark:text-gray-300 bg-transparent outline-hidden ${
											phoneNumberError
												? 'ring-1 ring-red-500 focus:ring-1 focus:ring-red-500'
												: ''
										}`}
										type="tel"
										inputmode="numeric"
										pattern="[0-9]*"
										value={formatPhoneInputValue(phoneNumber, phoneCountryCode)}
										placeholder={$i18n.t('Enter your phone number')}
										on:beforeinput={(event) => {
											if (event.data && /[^0-9]/.test(event.data)) {
												event.preventDefault();
											}
										}}
										on:keydown={(event) => {
											if (event.key.length === 1 && /[^0-9]/.test(event.key)) {
												event.preventDefault();
											}
										}}
										on:focus={handlePhoneFocus}
										on:input={handlePhoneInput}
										on:keydown={handlePhoneKeydown}
									/>
								</div>
							</div>
							{#if phoneNumberError}
								<div class="mt-1 text-xs text-red-500">{phoneNumberError}</div>
							{/if}
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
							<div class=" mb-1 text-xs font-medium">{$i18n.t('Work Hours (Availability)')}</div>

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
								<span class="text-xs text-gray-500">{$i18n.t('to')}</span>
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
