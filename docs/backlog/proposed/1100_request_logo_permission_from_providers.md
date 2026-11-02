# 1100 — Request logo permission from providers

> Package: AbstractFramework (root), AbstractUIC (ui-kit brand marks), AbstractGateway (console), website
> Type: task
> Created: 2026-11-02
> Priority: normal
> Labels: brand, trademark, legal, operator-action

## Summary

Ask each provider that requires permission for written approval to show its logo on a provider-selection card, then switch that card from a text badge back to the logo only after the approval is recorded. Until then the badge is text. The operator owns the sending (these are emails or forms in the operator's name); this item holds who to ask, what to send and what to record.

## Why

Operator ruling 2026-11-02: show a provider's logo only with permission; text badges meanwhile. Research: `untracked/council-2026-11-02/provider-logos-brand-rules.md` (rules per provider, legal frame, attribution text). Anthropic's guidelines (https://www.anthropic.com/legal/trademark-guidelines) allow its marks "only in materials we approve beforehand"; OVHcloud's policy says "The use of OVHcloud Logos always require the written permission of OVHcloud". Not a legal opinion.

Decision 2026-11-02: keep OpenAI, OpenRouter, Hugging Face, LM Studio and Mistral logos (their terms allow it); text badges for Anthropic, OVHcloud, Portkey, Ollama, DeepSeek, NVIDIA; site text-only; trademark footer line. Google, Meta and Microsoft marks also ship (model catalog, `brand_icons.tsx` ids `google`, `meta`, `microsoft`) and are listed below; no provider-specific "works with" page was found for them.

## Contacts and process (sources retrieved 2026-11-02 unless stated)

| Provider | Contact / process | Source URL | What to send |
|---|---|---|---|
| Anthropic | marketing@anthropic.com (named for "websites, or other uses" by a party with a business relationship); the page says Anthropic supplies the image files | https://www.anthropic.com/legal/trademark-guidelines | request text + screenshot of the card; ask them to supply the approved image |
| OVHcloud | legalbrand@ml.ovh.net (named in the contracting-parties guidelines, dated Dec 2024; confirm still current, found via search snippet, PDF not opened by me); policy: logos need written permission or a trademark licence | https://www.ovhcloud.com/sites/default/files/external_files/trademark_usage_guidelines_for_contracting-parties-30122024-english.pdf and https://www.ovhcloud.com/sites/default/files/external_files/trademark-usage-policy-en-30december-24.pdf | request text + screenshot; ask for a written licence or explicit written permission |
| Portkey | no public brand process found; terms page unreadable (https://portkey.ai/terms). Site says it is now part of Palo Alto Networks (PRISMA AIRS AI Gateway), so brand rights may sit with Palo Alto Networks. Routes seen: "Contact us" and https://portkey.ai/book-a-demo; press contact in the acquisition release: https://investors.paloaltonetworks.com/news-releases/news-release-details/palo-alto-networks-acquire-portkey-secure-rise-ai-agents | see left | operator picks the Contact us form; confirm the current owner first |
| Ollama | hello@ollama.com (listed for questions in the Terms); no brand guidelines page | https://ollama.com/terms | request text |
| DeepSeek | no brand or legal contact found; only a general address on the site, service@deepseek.com (security@ is for security reports only) | https://www.deepseek.com/en/ | request text; low expectation of an answer; text badge is the realistic outcome |
| NVIDIA | no process on the page ("expressly authorized in writing"); general https://www.nvidia.com/en-us/contact/ | https://www.nvidia.com/en-us/about-nvidia/legal-info/logo-brand-usage/ | request text; note NVIDIA says logo use "infers a partnership or endorsement" |
| Google / Gemini | no current Gemini page found; about.google brand page 404. General guidance entry: https://about.google/brand-resource-center/guidance/ (from a search result, not opened). Archived 2008 rule: written permission via a Permission Request Form | search only, 2026-11-02 | check the current guidance page, then use its request form |
| Meta / Llama | Meta Brand Resource Center "My Requests" process (professional or commercial uses; English only); Llama licence requires following Meta brand guidelines | https://www.meta.com/brand/resources/meta/company-brand/ and https://www.meta.com/brand/resources/meta/my-request/ (search results, not opened) | request via My Requests |
| Microsoft | "approval from an appropriate contact within Microsoft"; corporate logo needs authorization; no email found | https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks (403 to my fetch; via search) | contact the Trademark and Brand team through that page |

For Google, Meta and Microsoft the catalog marks are small model-maker avatars; the cheaper outcome is text badges (as for DeepSeek/NVIDIA) unless the operator wants to ask.

## Ready-to-send request text

> Subject: Permission to show the [Provider] logo in an open-source app
>
> Hello, I maintain AbstractFramework (https://abstractframework.ai), an MIT-licensed open-source AI framework that runs on the user's own machine. Users can connect their own [Provider] account or key. We would like to show the official [Provider] logo, unmodified and in its original colours, on the provider-selection card of the self-hosted console, only to identify the [Provider] service that card configures. The logo would never be larger than our own name, would not appear in advertising or on the website, and the app states that AbstractFramework is independent and not affiliated with or endorsed by [Provider]. Could you give us written permission, or point us to the official asset and your terms? Please also tell us if you require specific wording or a different asset. A screenshot of the card is attached. Thank you, [name], [contact]

## Scope

### In scope

- Operator sends the requests (or declines per provider); replies filed under `untracked/` with the date.
- Recording each approval in the repo (see acceptance), then switching that card's badge to the logo in `abstractuic/ui-kit/src/brand_icons.tsx` + `docs/icons.md`, regenerating the gateway islands bundle.

### Out of scope

- Any logo on abstractframework.ai (decided text-only).
- Providers whose terms already allow their logo (OpenAI, OpenRouter, Hugging Face, LM Studio, Mistral).

## Acceptance criteria

- [ ] Each of Anthropic, OVHcloud, Portkey, Ollama, DeepSeek, NVIDIA (and Google, Meta, Microsoft if asked) has a recorded outcome: approved, refused, or no answer.
- [ ] Each approval is recorded in the repo with date, scope (which surface, which asset, wording required) and the sender, in the `retrieved`/`restrictions` fields of the provider's `brand_icons.tsx` entry and its `docs/icons.md` row.
- [ ] A card switches from text badge to logo only after its approval is recorded; no approval, no logo.
- [ ] Any wording a provider requires is added to the in-app About and docs attribution line.

## Receipts

- Research: `/Users/albou/tmp/abstractframework/untracked/council-2026-11-02/provider-logos-brand-rules.md`
- Operator ruling 2026-11-02 (coordinator message).
