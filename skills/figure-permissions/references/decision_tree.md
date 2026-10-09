# Permissions decision tree

This is not legal advice. The rights holder or the journal's permissions desk decides close calls. Run `scripts/route_permission.py` and use its `action` string in the log. The names are:

```
not_required
fix_type
attribute
attribute_check_sharealike
credit_recommended
request_or_replace
reuse_unmodified_only
do_not_adapt
request_rightslink
check_agreement
stop_and_verify
```

Read the license on the version-of-record HTML page, not from a reposted PDF.

1. `original` + license `original`: use the figure. Credit `Created for this review.`
2. Type and license disagree (`fix_type`): stop and correct the ledger.
3. `unknown`: stop. Do not copy the figure.
4. `own-previous`: open the publishing agreement or the article license line, reclassify as `cc-by`, `publisher-owned`, or another value below, then route again.
5. `cc-by`: reuse or adapt with attribution. No permission request. Deed: https://creativecommons.org/licenses/by/4.0/
6. `cc-by-sa`: reuse or adapt only if the target journal can carry ShareAlike. If the journal requires a copyright transfer or a different license, do not use the figure. Deed: https://creativecommons.org/licenses/by-sa/4.0/
7. `cc-by-nc` and `cc-by-nc-sa`: both licenses allow adaptation. Do not decide that journal publication is non-commercial. Request written permission or replace the figure. Deeds: https://creativecommons.org/licenses/by-nc/4.0/ and https://creativecommons.org/licenses/by-nc-sa/4.0/
8. `cc-by-nd`: unmodified reuse with attribution is allowed. Adaptation is not. No crop, recolor, or relabel. Deed: https://creativecommons.org/licenses/by-nd/4.0/
9. `cc-by-nc-nd`: request permission or replace the figure. Do not adapt. Deed: https://creativecommons.org/licenses/by-nc-nd/4.0/
10. `cc0` or `public-domain`: no request. Still add a scholarly credit. https://creativecommons.org/publicdomain/zero/1.0/
11. `publisher-owned`: the user starts at the permission button on the article page (Copyright Clearance Center RightsLink when the publisher uses it: https://www.copyright.com/). The agent does not click, pay, or accept terms.

A redraw is `original` only when it does not reproduce the source's protected expression. Copyright covers expression, not the underlying facts (https://www.copyright.gov/circs/circ01.pdf). If a reader would recognize the same graphic, keep the row as `adapted`.

STM Permissions Guidelines are an agreement among signatory publishers, not a right an author grants themselves. Quotas and the signatory list must be read on the day of use at https://stm-assoc.org/what-we-do/core-services/ip-copyright/permissions/permissions-guidelines/. The 26 June 2024 text is linked from that page. Ask the target journal whether it will clear the figure under those guidelines, and keep their written answer. Do not reuse on the basis of the quota alone.
