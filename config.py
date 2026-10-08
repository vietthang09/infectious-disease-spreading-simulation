CONFIG = {
    "grid_width": 60,
    "grid_height": 40,
    "cell_size": 15,
    "initial_population": 800,
    "fps": 1,
    
    "p": 0.3, 
    "N": 5,  
    "sick_duration": 5,
    "d": 0.2,  
    "s": 0.8,
    "flat_infection_rate": True,  # False: 1 - (1-p)^k (theo số hàng xóm S). True: cố định là p dù gặp bao nhiêu người S
    "num_seeds": 10,              # Số lượng hạt giống ngẫu nhiên (seeds) chạy lặp lại
    "export_seed_plots": True,    # True: Xuất thêm các biểu đồ chi tiết cho từng seed riêng biệt
}

COLORS = {
    "BACKGROUND": (20, 20, 20),
    "GRID_LINE": (40, 40, 40),
    "H": (46, 204, 113),
    "I": (241, 196, 15),
    "S": (231, 76, 60),
    "R": (149, 165, 166),
}
