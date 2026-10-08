các biến: 
p: 0.3
N: 5
T_sick: 7
lặp lại 20 lần

2 xu hướng:
- Số ca tử vong tăng tuyến tính: Khi d tăng từ 0.0 lên 0.9, tổng số người chết tăng từ 0 đến 260 người.
- Thời gian dịch diễn biến phi đơn điệu (non-monotonic): bắt đầu ở mức cao 99.6 bước (d = 0.0), giảm xuống đáy 93.9 bước (d = 0.4), rồi tăng dần trở lại đến 103 bước (d = 0.9):
+ Tỉ lệ chết 40% đủ nhanh để loại bỏ các cá thể bệnh. Các ô trống, kết hợp với 60% người khỏi bệnh có kháng thể tạo thành hàng rào chia cắt mầm bệnh với các cá thể khỏe mạnh => Dịch bệnh tự hết => Thời gian dịch bệnh giảm
+ Khi d tiến sát tới 0.9, nhiều cá thể bệnh bị chết và loại bỏ nhanh chóng, làm cho không gian thưa thớt => Mầm bệnh phải duy chuyển rất xa mới gặp được cá thể khỏe mạnh => Dịch bệnh kéo dài âm ỉ
