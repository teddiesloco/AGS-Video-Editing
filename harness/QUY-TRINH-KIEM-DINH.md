# Quy trình kiểm định: render → lấy mẫu → soát → sửa

Áp dụng cho mọi video AGS trước khi bàn giao. Lệnh chạy từ thư mục gốc repo (hoặc thư mục skill khi dùng bản zip).

## 1. Chạy harness kèm contact sheet
```bash
python harness/ags_anti_slop_guard.py <video.mp4> --contact-sheet <video>_sheet.jpg [--frames 12]
```
| Mã thoát | Nghĩa | Việc phải làm |
|---|---|---|
| `0` | ĐẠT | Soát contact sheet (bước 2) rồi bàn giao |
| `2` | CẢNH BÁO | Đọc từng dòng cảnh báo, sửa (bước 3) hoặc báo rõ cho người dùng |
| `1` | LỖI | Không bàn giao; sửa và render lại |

Ngưỡng (khai báo ở đầu `harness/ags_anti_slop_guard.py`):
- LỖI: không đọc được / không có hình / ngắn hơn 1 s; đen ≥ 90% thời lượng; đứng hình ≥ 90%; có luồng tiếng nhưng câm ≥ 90%.
- CẢNH BÁO: không có tiếng; lệch độ dài hình-tiếng > 0.25 s; âm lượng ngoài -14 ± 2 LUFS; true peak > -1.0 dBTP;
  đoạn đen ≥ 0.5 s; đứng hình ≥ 5 s; khoảng lặng dưới -50 dBFS ≥ 2 s.
- Dòng `[Đo]` in thời lượng, LUFS, true peak, độ lệch hình-tiếng — dùng cho báo cáo bàn giao.

## 2. Soát contact sheet bằng mắt (hoặc model thị giác)
Mở ảnh contact sheet (ô `#0` là khung 0, các ô sau rải đều tới cuối; video dọc có khung hồng = vùng an toàn 9:16).
Chấm từng tiêu chí:
1. **Hook ở khung 0:** video có hook thì ô `#0` phải thấy rõ chữ hook, đủ đậm.
2. **Vùng an toàn:** mọi chữ (phụ đề, hook, nhãn, ticker) nằm trong khung hồng.
3. **Chữ tiếng Việt:** đủ dấu, không ô vuông, không vỡ dấu, không tràn mép, không chồng chéo.
4. **Chủ thể:** mặt người nói nằm trong khung ở mọi ô (video reframe/short); người không bị cắt mất đầu.
5. **Hình:** không ô đen, không ô trùng lặp bất thường (đứng hình), không méo tỉ lệ.
6. **Karaoke:** ở các ô có lời, thấy một từ được tô màu khác.

## 3. Sửa rồi lặp lại (tối đa 3 vòng)
| Dấu hiệu | Cách sửa |
|---|---|
| LUFS / true peak lệch | Chạy lại script (đều chuẩn hoá -14 LUFS); video từ `/ags-edit-hook` thì chạy thêm `/ags-edit-editorial` |
| Khoảng lặng dài | `/ags-edit-az` (tăng `--threshold-db`, ví dụ -20) rồi dựng lại |
| Đứng hình / đen | Kiểm tra nguồn; slideshow BĐS: thêm ảnh hoặc rút `--seconds` |
| Chữ ra ngoài vùng an toàn | Rút ngắn chữ (hook, nhãn, ticker); BĐS: dời tọa độ polygon/ô lô vào vùng an toàn |
| Mặt bị lệch khung | Kiểm tra video có nhiều người; dùng `--no-reframe` nếu không có mặt rõ |
| Sai chữ / sai dấu do bóc băng | Dùng model lớn hơn: `--model small` hoặc `--model large-v3-turbo` |

Sau 3 vòng vẫn chưa đạt: dừng, báo người dùng cảnh báo còn lại kèm đường dẫn contact sheet.

## 4. Báo cáo bàn giao
`[Video đầu ra] -> [Thời lượng] -> [LUFS] -> [Kết quả guard (exit)] -> [Contact sheet]`
