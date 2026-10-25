# Conversational marketing review
[Goal and source] → [Plan with source cuts, proof and CTA] → [Draft + findings] → [Approve or revise] → [Final files]

| # | Thành phần | Kiểu | Quy tắc Hiển thị, Ràng buộc & Xử lý Sự kiện |
|---|---|---|---|
| 1 | marketing-goal (`data-testid="marketing-goal"`) | Text | Audience, objective, allowed claims; do not invent |
| 2 | marketing-plan (`data-testid="marketing-plan"`) | Review | Source intervals, role allocation and caption style |
| 3 | marketing-draft (`data-testid="marketing-draft"`) | Media | Draft path and technical findings; not final |
| 4 | marketing-approval (`data-testid="marketing-approval"`) | Action | Explicit owner confirmation bound to content hash |
| 5 | marketing-status (`data-testid="marketing-status"`) | Status | Loading / Empty / Error / Populated |

Empty requests local source. Loading displays stage. Error shows E-ags-marketing-editor-* and repair guidance. Populated shows reviewable artifacts and asks approval. At mobile 360/390/430 all controls stack, no horizontal overflow; desktop >=1280 uses bounded readable width. This models host chat, not a new deployed app.

Responsive: Mobile <768px uses stacked controls; Tablet 768–1279px retains one readable column; Desktop >=1280px caps content width. Verify 360/390/430px and 1280px.
