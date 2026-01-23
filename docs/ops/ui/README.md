# UI Ops

## Form Save/Discard CN Labels

Change:
- Add Chinese labels to form Save/Discard buttons in Odoo 17 backend.
- UI-only change (no behavior change).

Upgrade:
```
odoo -d <db> -u smart_construction_core --stop-after-init
```

Verify:
- Enter edit mode on any form (e.g. project.project create).
- Buttons show text: "保存" and "放弃变更".
- Browser hard refresh (Ctrl+F5) if assets are cached.
