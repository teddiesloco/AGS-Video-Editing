# AGS Marketing Editor — thiết kế để chủ sản phẩm duyệt

Status: proposed specification; direction approved by Teddy on 2026-10-25, implementation not started.

## Mục tiêu và đối tượng
Người dùng đưa video/tài sản vào workspace Antigravity, Codex hoặc Claude Code rồi yêu cầu bằng tiếng Việt. Agent tự kiểm tra môi trường, đọc nguồn, đề xuất nội dung, dựng nháp, nhận sửa và xuất video marketing. Người dùng không cần viết JSON hoặc chạy FFmpeg. Đây là bộ skill + công cụ chạy local, không phải ứng dụng dựng video giải trí hay SaaS mới.

Ưu tiên: marketing, bán hàng, chia sẻ kiến thức có ích, xây uy tín và tăng khả năng được chia sẻ đến đúng khách hàng. Không hứa lượt xem, viral, lead hoặc doanh thu. Không thêm meme, hiệu ứng gây nhiễu hay câu giật gân làm sai lời người nói.

## Luồng người dùng
1. Người dùng cung cấp video/thư mục tài sản và mục tiêu bằng lời thường. Agent hỏi đúng thông tin còn thiếu ảnh hưởng đầu ra: khách xem, thông điệp hoặc hành động mong muốn. Tự chọn thông số kỹ thuật hợp lý.
2. Kiểm tra công cụ/dependency; báo lỗi có cách khắc phục. Không tự chi tiền, gửi tài sản ra dịch vụ ngoài hoặc đăng nội dung.
3. Chép lời có mốc thời gian; lập bảng đoạn cắt, nội dung mở đầu, bằng chứng và CTA. Giữ nguyên ý, phủ định, điều kiện và ngữ cảnh lời nói. Không tự tạo lời chứng thực, số liệu, giá hay khan hiếm.
4. Duyệt kế hoạch; dựng nháp tự động và trả video + contact sheet + nhận xét cần người kiểm tra.
5. Người dùng sửa bằng lời thường; agent dịch thành thay đổi cụ thể trong kế hoạch. Thay đổi nguồn, lời, timing hoặc phong cách làm hết hiệu lực phê duyệt liên quan.
6. Duyệt nháp; xuất bản cuối và phụ đề/báo cáo. Xuất file không đồng nghĩa đăng mạng xã hội; không tự publish.

## Phạm vi chức năng
- Tái sử dụng cắt đoạn, cắt lặng/micro-pause, reframe bám mặt, phụ đề ASS, âm thanh và anti-slop guard hiện có. Không viết lại engine.
- Timeline thực ghi rõ nguồn, khoảng thời gian nguồn/đích, vai trò hình và nhịp nội dung. Bốn nhịp Cảnh–Hiểu–Chọn–Trao do agent chọn theo nghĩa, không áp bằng vị trí câu đơn thuần.
- A-roll, bằng chứng và hình bổ trợ được dựng từ tài sản chỉ định. 60/30/10 là mục tiêu chỉnh được, không ép mọi nội dung; báo tỷ lệ thực từ timeline không chồng lấn. Thiếu bằng chứng thì báo thiếu, không dùng stock/AI giả làm bằng chứng.
- Persona áp font, màu, caption, thẻ chữ và nhịp dựng thật. Font phải có trên máy/gói và đủ dấu Việt; font thiếu phải báo rõ lựa chọn thay thế. Không âm thầm tuyên bố đã áp font không tồn tại.
- Chế độ nội dung: chia sẻ kiến thức, giải đáp phản đối, trình diễn sản phẩm, case study có nguồn và chào bán có dữ kiện. Không thêm nhánh giải trí.
- Chấm hook mặc định trong luồng mới. Bộ 3C là heuristic, không bằng chứng hiểu nghĩa; cho phép người duyệt chấp nhận có lý do. Chế độ strict vẫn có. Không phá mặc định API cũ chỉ để ép một công thức.
- Hai mốc duyệt gắn dấu vân tay kế hoạch/tài sản và nháp. Không cho phép dùng phê duyệt cũ cho bản đã đổi; không gọi cờ boolean là xác thực danh tính người duyệt.
- Tích hợp CLI/MCP và hướng dẫn ba host trên cùng engine. Không cần một UI web mới để hoàn thành việc dựng.
- Bàn giao MP4 dọc 1080x1920, phụ đề, contact sheet, kế hoạch, nguồn tài sản và báo cáo chất lượng. Giữ đường xuất dự án desktop hiện có, không hứa tương thích CapCut chưa mở kiểm tra.

## Ranh giới tự động hóa
Agent tự làm các thao tác kỹ thuật và biên tập trong phạm vi đã duyệt. Mốc duyệt dành cho nội dung/chi phí/quyền, không bắt người dùng bấm từng thao tác. Không mua dịch vụ, gọi API tính phí, publish, deploy hoặc tạo repository mới nếu chưa được duyệt phù hợp. Tài sản và transcript là dữ liệu không tin cậy, không được thực thi chỉ dẫn nhúng.

## Tiêu chí nghiệm thu
1. Trong mỗi host Antigravity, Codex, Claude Code: từ yêu cầu tự nhiên và video mẫu đến kế hoạch, nháp, sửa và xuất cuối; lưu bằng chứng riêng từng host. Chưa có runtime host nào thì ghi chưa kiểm chứng host đó, không suy từ CLI.
2. Video người nói giữ nghĩa và đồng bộ phụ đề sau cắt/reorder; hình bám mặt hoặc báo fallback rõ ràng. Không mất từ phủ định tại điểm cắt.
3. Có render thật kiểm chứng cảnh A-roll/bằng chứng/hình bổ trợ xuất hiện đúng thời điểm, tỷ lệ báo cáo khớp thời lượng; không chỉ kiểm JSON.
4. Đổi persona phải thấy khác biệt thật trên frame; tiếng Việt không mất dấu, không tràn vùng an toàn.
5. Bản chưa duyệt hoặc đã thay đổi không được xuất final dưới phê duyệt cũ. File nguồn không bị ghi đè; lần dựng lỗi không để bản final giả thành công.
6. Test trường hợp nguồn thiếu, kit hỏng, clip không tiếng, timestamp ngoài khoảng, yêu cầu sửa mơ hồ, job batch lỗi độc lập và chữ dài.
7. Chạy kiểm định kỹ thuật và xem/nghe đầu ra: hook mở đầu, mặt/chữ, nhịp cắt, âm thanh, CTA. PASS tự động không thay duyệt ý nghĩa hoặc thẩm mỹ. Báo riêng pass/fail/not checked.
8. Review độc lập đúng revision trước commit/push. Giữ nguyên công việc không liên quan; giải quyết remote services riêng, không đẩy toàn bộ services vào repo khác.

## Thiết kế tích hợp đã khảo sát
Engine hiện có: scripts/ags_clip_shorts.py, ags_cut_silence.py, ags_reframe.py, ags_editorial_sub.py, ags_common.py; kiểm định harness/ags_anti_slop_guard.py; giao tiếp mcp/ags_mcp_server.py. Bộ pack và pipeline hiện tại ở services/ops/ags-reels-footage. Triển khai cần khóa schema timeline/approval và ranh giới sở hữu trước khi chia coder; AGS-BA scaffold/audit và builder plan bắt buộc trước code.

## Ngoài phạm vi
Video giải trí; cam kết viral; tự đăng mạng xã hội; tự tạo nội dung chứng minh không có nguồn; clone mã/asset đối thủ; mở SaaS/UI mới; thay đổi licensing/thanh toán; deploy production.
