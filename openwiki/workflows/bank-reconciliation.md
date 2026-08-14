---
type: workflow
title: Bank reconciliation workflow
description: Importing bank CSV data, suggesting categories, matching transactions, and exporting reconciliation results.
tags: [workflow, reconciliation]
---

# Bank reconciliation workflow

Electron selects a CSV through `DataStore.chooseBankCsv`, decodes it, and passes rows to the renderer reconciliation flow. Parsing supports common German separators, encodings, dates, and decimal formats. Matching compares amount within €0.02 and exact date or a three-day fuzzy window, producing matched/possible/missing statuses; category suggestions use payee and purpose keywords. The user applies accepted matches through normal document saves. Python provides the parallel `reconciliation_service.py` path. Tests are in the TypeScript reconciliation suite and Python service-adjacent behavior.
