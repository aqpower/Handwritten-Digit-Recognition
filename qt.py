import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout
from PyQt5.QtGui import QImage, QPainter, QPen, QPixmap
from PyQt5.QtCore import Qt, QPoint
import torch
from ResNet18 import ResNet, Block
import torchvision.transforms as transforms
import time
from PyQt5.QtWidgets import QMessageBox

class DrawingWidget(QWidget):
    def __init__(self, parent=None):
        super(DrawingWidget, self).__init__(parent)
        self.setFixedSize(280, 280)
        self.image = QImage(self.size(), QImage.Format_RGB32)
        self.image.fill(Qt.black)
        self.drawing = False
        self.lastPoint = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.lastPoint = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton & self.drawing:
            painter = QPainter(self.image)
            painter.setPen(QPen(Qt.white, 20, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(self.lastPoint, event.pos())
            self.lastPoint = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def paintEvent(self, event):
        canvasPainter = QPainter(self)
        canvasPainter.drawImage(self.rect(), self.image, self.image.rect())

    def clearImage(self):
        self.image.fill(Qt.black)
        self.update()

    def getImage(self):
        return self.image

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.drawing_widget = DrawingWidget()
        self.predict_button = QPushButton("Predict")
        self.clear_button = QPushButton("Clear")
        self.device_label = QLabel("Device: ")
        self.device_label.setStyleSheet("font-size: 20px;")
        self.result_label = QLabel("识别为: ")
        self.result_label.setStyleSheet("font-size: 20px;")
        self.prediction_time_label = QLabel("识别时间: 0ms")  # 添加显示识别时间的label
        self.prediction_time_label.setStyleSheet("font-size: 20px;")
        self.correct_predictions = 0  # 正确识别的次数
        self.total_predictions = 0  # 总识别次数
        self.accuracy_label = QLabel("正确率: N/A")  # 添加显示正确率的label
        self.accuracy_label.setStyleSheet("font-size: 20px;")

        self.predict_button.clicked.connect(self.predict)
        self.clear_button.clicked.connect(self.drawing_widget.clearImage)

        layout = QVBoxLayout()
        layout.addWidget(self.drawing_widget)
        layout.addWidget(self.predict_button)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.device_label)
        layout.addWidget(self.result_label)
        layout.addWidget(self.prediction_time_label)  # 将新的label添加到布局中
        layout.addWidget(self.accuracy_label)  # 将正确率的label添加到布局中

        self.setLayout(layout)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.device_label.setText(f"Device: {self.device}")
        self.model = torch.load("model_06月26日23:12.pth")
        self.model.to(self.device)

        self.model.eval()

    def predict(self):
        start_time = time.time()  # 获取预测开始时间
        qimage = self.drawing_widget.getImage()
        image = qimage.convertToFormat(QImage.Format_Grayscale8)
        ptr = image.bits()
        ptr.setsize(image.byteCount())
        arr = np.frombuffer(ptr, np.uint8).reshape((image.height(), image.width()))

        arr = arr.astype(np.float32) / 255.0
        arr = np.expand_dims(arr, axis=0)
        arr = np.expand_dims(arr, axis=0)

        tensor = torch.from_numpy(arr)
        tensor =  transforms.Resize((28,28))(tensor)

        with torch.no_grad():

            tensor = tensor.to(self.device)
            output = self.model(tensor)

            pred = output.argmax(dim=1, keepdim=True).item()
            self.result_label.setText(f"识别为: {pred}")

            end_time = time.time()  # 获取预测结束时间
            prediction_time = (end_time - start_time) * 1000  # 计算预测时间并转换为毫秒
            self.prediction_time_label.setText(f"识别时间: {prediction_time:.2f}ms")  # 更新显示的识别时间
        # 弹窗询问是否识别正确
        reply = QMessageBox.question(
            self,
            "识别结果确认",
            f"识别结果是: {pred}\n识别是否正确？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        self.total_predictions += 1  # 更新总识别次数
        if reply == QMessageBox.Yes:
            self.correct_predictions += 1  # 如果识别正确，更新正确识别次数

        # 计算并更新正确率
        accuracy = (self.correct_predictions / self.total_predictions) * 100
        self.accuracy_label.setText(f"正确率: {accuracy:.2f}%")

app = QApplication(sys.argv)
main_window = MainWindow()
main_window.show()
sys.exit(app.exec_())
