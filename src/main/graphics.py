from PIL import ImageFont

class Graphics:
    def __init__(self, device):
        self.device = device
    
        self.fontSelected = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
        self.fontUnselected = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 8)

        self.lineSpacing = 3

    def draw_centered_lines(self, draw, lines): # lines = [(text, selected), ...]
        # measure all lines
        heights = []
        widths = []
        fonts = []

        for text, selected in lines:
            font = self.fontSelected if selected else self.fontUnselected
            bbox = draw.textbbox((0, 0), text, font=font)

            widths.append(bbox[2] - bbox[0])
            heights.append(bbox[3] - bbox[1])
            fonts.append(font)

        totalHeight = sum(heights) + (len(lines) - 1) * self.lineSpacing

        # center vertically
        y = (self.device.height - totalHeight) // 2

        # draw each line
        for i, (text, selected) in enumerate(lines):
            textWidth = widths[i]
            font = fonts[i]

            x = (self.device.width - textWidth) // 2

            draw.text((x, y), text, font=font, fill=255)

            y += heights[i] + self.lineSpacing
            
    def draw_lines(self, draw, lines, startY=0): # lines = [text, ...]
        y = startY
        font = self.fontSelected

        for text in lines:
            draw.text((0, y), text, font=font, fill=255)

            bbox = draw.textbbox((0, 0), text, font=font)
            height = bbox[3] - bbox[1]

            y += height + self.lineSpacing
