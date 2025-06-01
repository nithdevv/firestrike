import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
plt.style.use('dark_background')

def mandelbrot(h, w, max_iter, x_min, x_max, y_min, y_max):
    y, x = np.ogrid[y_min:y_max:h*1j, x_min:x_max:w*1j]
    c = x + y*1j
    z = c
    divtime = max_iter + np.zeros(z.shape, dtype=int)

    for i in range(max_iter):
        z = z**2 + c
        diverge = z*np.conj(z) > 2**2
        div_now = diverge & (divtime == max_iter)
        divtime[div_now] = i
        z[diverge] = 2

    return divtime

def animate_mandelbrot(h=500, w=750, max_iter=100):
    # Интересные точки для зума
    zoom_points = [
        (-2, 0.8, -1.4, 1.4),  # Полный вид
        (-0.7, -0.5, -0.1, 0.1),  # Первый зум
        (-0.745, -0.735, -0.1, -0.09),  # Второй зум
        (-0.743, -0.742, -0.097, -0.096),  # Третий зум
    ]
    
    frames = 50  # Количество кадров для каждого зума
    
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111)
    
    def update(frame):
        ax.clear()
        zoom_index = frame // frames
        progress = (frame % frames) / frames
        
        if zoom_index >= len(zoom_points) - 1:
            current = zoom_points[-1]
        else:
            current = zoom_points[zoom_index]
            next_point = zoom_points[zoom_index + 1]
            
            # Интерполяция между точками
            x_min = current[0] + (next_point[0] - current[0]) * progress
            x_max = current[1] + (next_point[1] - current[1]) * progress
            y_min = current[2] + (next_point[2] - current[2]) * progress
            y_max = current[3] + (next_point[3] - current[3]) * progress
            current = (x_min, x_max, y_min, y_max)
        
        img = mandelbrot(h, w, max_iter, *current)
        im = ax.imshow(img, cmap='hot', extent=[current[0], current[1], current[2], current[3]])
        ax.set_title(f"Множество Мандельброта (Зум {zoom_index + 1})")
        fig.colorbar(im, ax=ax, label='Количество итераций')
        ax.set_xlabel('Re(c)')
        ax.set_ylabel('Im(c)')
        return [im]

    anim = FuncAnimation(
        fig, 
        update, 
        frames=len(zoom_points) * frames,
        interval=50,
        repeat=True
    )
    
    plt.show(block=True)

if __name__ == "__main__":
    animate_mandelbrot() 