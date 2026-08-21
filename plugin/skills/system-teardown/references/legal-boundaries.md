# Legal and ethical boundaries

Orientation, not legal advice. Jurisdictions differ, several decisions cited here are
district-level, vacated, or on appeal, and this area is moving quickly. For anything
commercially consequential the answer is a lawyer, not this file.

The useful frame: **the technique is usually lawful; the access path and the use of the
artifact are what create liability.** Two teardowns using identical tools can sit on opposite
sides of the line depending on how the target was reached and what was done with the result.

## Quick classification

| Clearly observation | Grey — get authorization or counsel | Over the line |
|---|---|---|
| Loading public pages in a normal browser | Bulk automated scraping at scale | Fake or pretextual accounts |
| Reading headers, HTML, JS, sourcemaps the server serves | Scraping while logged into your own paid account | Accessing another user's data; ID enumeration |
| DevTools inspection of your own session | Ignoring `robots.txt` | Continuing after a cease-and-desist or IP block |
| Public spec files, `.well-known/`, sitemap | Republishing scraped content | Circumventing auth, rate limits, WAF, bot defenses |
| Vendor tools (Wappalyzer, BuiltWith, Similarweb) | Collecting personal data (GDPR/CCPA apply independently) | Credential stuffing; fuzzing; unauthorized vulnerability testing |
| Analyzing a binary you lawfully own, for interoperability | Analysis prohibited by an EULA you accepted | Circumventing DRM or license enforcement |
| Reconstructing a system you own or operate | Vendor evaluation under a license permitting testing | Extracting a third party's proprietary prompt to copy it |

## United States

### CFAA

***Van Buren v. United States*, 594 U.S. 374 (2021)** adopted a **gates-up-or-down** reading of
"exceeds authorized access": liability attaches when you access areas of a system you are not
entitled to access at all, not when you misuse information you were entitled to obtain.
Purpose-based theories were rejected — an improper motive does not create liability for
information you had the right to get.

**What it did not decide, and this matters.** Footnote 8 expressly reserves the question:
*"we need not address whether this inquiry turns only on technological (or 'code-based')
limitations on access, or instead also looks to limits contained in contracts or policies."*
Whether terms of service can define the gates is still being litigated. Do not plan an
engagement on the belief that ToS can never matter under the CFAA — the Court declined to
say that.

***hiQ Labs v. LinkedIn*** (9th Cir., reaffirmed 18 April 2022 after GVR in light of
*Van Buren*) held that scraping data **publicly available without authentication** *likely*
is not access "without authorization." Note the posture: this was a **preliminary injunction**
— "serious questions going to the merits," not a merits judgment.

**Do not cite hiQ as "scraping is legal," and do not cite it as "the CFAA claim failed."**
In the December 2022 stipulated judgment hiQ conceded **CFAA liability**, California Penal
Code §502 liability, breach of the User Agreement, trespass to chattels, and misappropriation
— paid **$500,000**, and accepted a permanent injunction requiring destruction of the scraped
data *and the algorithms derived from it*. The trigger was **fake accounts accessing
password-protected content**.

The lesson is not that contracts beat the CFAA. It is that the public-data theory survived and
the fake-account conduct did not. That is why fake accounts sit in this skill's refusal list.

***Ryanair DAC v. Booking Holdings*** (D. Del.) is frequently miscited and the current state
matters. A jury returned a CFAA verdict in August 2024 at exactly the $5,000 statutory loss
floor. On **22 January 2025 the court granted judgment as a matter of law to Booking.com and
vacated it**, holding that the jury instruction permitting generic investigation and response
costs to count as CFAA "loss" absent technological harm was erroneous — only roughly $2,457 of
claimed loss was cognizable, below the threshold. The case is on appeal to the Third Circuit.

So: **investigation costs alone do not clear the CFAA loss threshold.** The durable lesson from
Ryanair is not the vacated verdict but the exposure — fake accounts and logged-in access are
what kept the claim alive to trial at all.

### Contract

***Meta Platforms v. Bright Data***, No. 23-cv-00077-EMC (N.D. Cal., 23 Jan 2024): summary
judgment for Bright Data on breach of contract. Meta's terms bind "users," and a **logged-out**
scraper is not using the service; Meta had previously had logged-out-visitor language and had
removed it. A perpetual survival clause purporting to bind former account holders was held
unenforceable for want of reasonable temporal or geographic limits. Meta dismissed its
remaining claim and waived appeal, so the ruling stands — but it remains one district-court
decision.

The operating rule that falls out: **logged-out changes the analysis; logged-in almost always
means the terms bind you.**

### Copyright — intermediate copying

***Sega v. Accolade*** (9th Cir. 1992) and ***Sony v. Connectix*** (9th Cir. 2000) are the
controlling US authority that **intermediate copying during reverse engineering is fair use**
where it is necessary to access unprotected functional elements and the purpose is
interoperability. This is what makes binary teardown lawful in the US at all, and it is the
pair most worth citing for the binary target.

***Google v. Oracle*** (2021) held that reimplementing an API's **declaring code** for a
transformative purpose was fair use. Directly load-bearing for the rebuild-plan path — but it
turned on the declaring/implementing distinction and on transformativeness, not on a general
right to reimplement.

### DMCA §1201(f)

Circumventing technical protection measures is prohibited, but §1201(f) exempts a person who
has lawfully obtained the right to use a program and circumvents **for the sole purpose of**
identifying and analyzing elements necessary to achieve interoperability with an independently
created program, where those elements were not otherwise readily available. (f)(2) covers
developing the means; (f)(3) permits sharing results **solely** for interoperability.

The exemption is narrow. It covers interoperability. It does not cover "we wanted to see how it
worked" or competitive copying.

### Trade secret (DTSA)

18 U.S.C. §1839(6)(B) is explicit, not merely permissive: improper means *"does not include
reverse engineering, independent derivation, or any other lawful means of acquisition."*
Reverse engineering a lawfully obtained product is not misappropriation.

This is the doctrine that makes legitimate teardown possible — and it is exactly the protection
that fake accounts, circumvention, or unauthorized access forfeit. Note the contrast with the
EU below: **the DTSA safe harbor does not override a contractual anti-reverse-engineering
clause in the US.**

## European Union

**Software Directive (2009/24/EC).**

- **Article 5(3)** — a lawful user may observe, study, and test the functioning of a program to
  determine the ideas and principles underlying any element, while performing acts they are
  entitled to perform.
- **Article 6** — decompilation is permitted where indispensable to obtain the information
  needed for **interoperability** of an independently created program: performed by a licensee
  or authorized person, the information not already readily available, confined to the
  necessary parts. The information may not be used for anything else, given to third parties,
  nor used to develop a substantially similar program.
- **Article 8** — *"Any contractual provisions contrary to Article 6 or to the exceptions
  provided for in Article 5(2) and (3) shall be **null and void**."*

Article 8 is the key structural difference from US practice: **an EULA cannot validly forbid
what Article 6 permits.** In the US, a contract can.

Also relevant: GDPR wherever personal data is touched, the sui generis **database right**, and
the DSM Directive's text-and-data-mining regime with its **Article 4 opt-out** — a
machine-readable opt-out is what makes automated collection unlawful in the EU that would be
arguable in the US.

## AI systems

System prompt extraction is **OWASP LLM07:2025 — System Prompt Leakage**. OWASP's framing:
*"the system prompt should not be considered a secret, nor should it be used as a security
control."* Legitimate on your own or authorized systems; an attack elsewhere.

The unresolved middle: providers' terms often prohibit exactly the activity safety research
requires, and researchers face statutory exposure plus account termination. There is an active
push for legal and technical safe harbors for good-faith AI evaluation, and parts of industry
have adopted them. Treat the presence of a safe harbor for the specific target as a fact to
check, not to assume.

Operating rule: apply extraction techniques only where the requester owns the system or holds
written authorization. Otherwise, architecture inference from ordinary permitted use.

## Clean-room procedure

**Trigger on contamination, not on ambition.** A user who has only used a competitor's product
normally has contaminated nobody and does not need a clean room. Ask the contamination question
before imposing the procedure:

> Has anyone who will write the new system read the target's source code, decompiled output,
> recovered sourcemaps, or an extracted system prompt?

If no — no clean room is required. Proceed to the rebuild plan normally, noting in §0 that no
contamination occurred and why.

If yes — the people who read it are contaminated. Code they subsequently write is exposed to a
copying claim regardless of how independently they believe they wrote it. Then:

1. **Analysis team** examines the target. They may read source, decompile, extract, trace.
2. **They produce a functional specification only** — what the system does, its interfaces,
   behaviors, formats. No implementation detail, no code fragments, no distinctive naming, no
   structural choices that were not functionally forced.
3. **A third party reviews the specification** and strips anything expressive rather than
   functional. This review is what makes the wall credible later.
4. **Implementation team** has never seen the target. They build from the specification alone.
5. **Document the wall as it happens** — who was on which side, what crossed, when, who
   reviewed it. A clean room reconstructed after the fact convinces nobody.

Under EU Article 6 the constraint is stricter: information obtained by decompilation may not be
used to develop a substantially similar program at all.

**Scale the ceremony to the team.** A two-person startup cannot staff two walled teams. For
them the practical version is: the person who read the target writes the functional
specification and then does not write the implementation of the parts they read; if that is
impossible, do not read the source in the first place. Say this rather than presenting a
procedure the user demonstrably cannot follow — an unusable safeguard is one they will ignore
entirely.
