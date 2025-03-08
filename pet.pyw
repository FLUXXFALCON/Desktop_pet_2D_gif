import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QListWidget, QListWidgetItem, QCheckBox
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QMovie, QPixmap, QIcon

class DesktopPet(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint)  # Başlık çubuğu olmayan pencere
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # Şeffaf arka planı etkinleştiriyoruz
        self.setWindowOpacity(1.0)  # Opaklık ayarı, tamamen görünür yapıyoruz

        self.pet_label = None
        self.pet_movie = None
        self.pet_data = self.load_pet_data()  # Pet verilerini yükle

        # Pet eklenmeden önce GUI
        self.main_widget = QWidget(self)
        self.main_widget.setStyleSheet("background-color: white;")  # Arka planı beyaz yapıyoruz
        self.layout = QVBoxLayout(self.main_widget)

        self.apply_button = QPushButton("Uygula", self.main_widget)
        self.apply_button.clicked.connect(self.apply_pet)
        self.layout.addWidget(self.apply_button)

        self.add_pet_button = QPushButton("Pet Ekle", self.main_widget)
        self.add_pet_button.clicked.connect(self.select_pet)
        self.layout.addWidget(self.add_pet_button)

        self.delete_pet_button = QPushButton("Seçili GIF'i Sil", self.main_widget)
        self.delete_pet_button.clicked.connect(self.delete_pet)
        self.layout.addWidget(self.delete_pet_button)

        self.bg_checkbox = QCheckBox("Arka Planı Kaldır", self.main_widget)
        self.layout.addWidget(self.bg_checkbox)

        self.pet_list_widget = QListWidget(self.main_widget)
        self.load_pet_list()  # Pet listelerini yükle
        self.layout.addWidget(self.pet_list_widget)

        self.setCentralWidget(self.main_widget)

        # Mouse sürükleme
        self.dragging = False
        self.drag_position = QPoint()

    def resizeEvent(self, event):
        """Pencere yeniden boyutlandırıldığında, pencere boyutunu güncelle."""
        if self.pet_movie:
            self.resize(self.pet_movie.currentImage().size())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.drag_position)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def apply_pet(self):
        """Uygula butonuna basıldığında pet'i ekle."""
        selected_pet = self.pet_list_widget.currentItem()
        if selected_pet:
            pet_name = selected_pet.text()
            self.load_pet_by_name(pet_name)
            self.main_widget.setParent(None)  # GUI kayboluyor
            self.show_pet()

    def select_pet(self):
        """Pet eklemek için bir GIF dosyası seç."""
        file_name, _ = QFileDialog.getOpenFileName(self, "GIF Seç", "", "GIF Files (*.gif)")
        if file_name:
            # Pet verisini kaydedelim
            pet_name = os.path.basename(file_name)
            self.pet_data[pet_name] = {'file': file_name, 'x': 100, 'y': 100}
            self.save_pet_data()  # Pet verisini kaydet

            # Pet listesine yeni peti ekleyelim
            self.load_pet_list()

    def delete_pet(self):
        """Seçili peti sil.""" 
        selected_pet = self.pet_list_widget.currentItem()
        if selected_pet:
            pet_name = selected_pet.text()

            # Pet'i sil
            if pet_name in self.pet_data:
                del self.pet_data[pet_name]
                self.save_pet_data()  # Pet verilerini kaydedelim

                # Pet listesini güncelle
                self.load_pet_list()

                # Eğer şu anda o pet görüntüleniyorsa, onu da gizle
                if self.pet_label and self.pet_label.movie().fileName().split("/")[-1] == pet_name:
                    self.pet_label.hide()
                    self.pet_label = None
                    self.pet_movie = None

    def load_pet_by_name(self, pet_name):
        """Seçilen peti yükle."""
        if pet_name in self.pet_data:
            pet_info = self.pet_data[pet_name]
            self.pet_movie = QMovie(pet_info['file'])

            self.pet_label = QLabel(self)
            self.pet_label.setMovie(self.pet_movie)
            
            # Checkbox durumuna göre arka planı ayarlıyoruz
            if self.bg_checkbox.isChecked():
                self.pet_label.setStyleSheet("background: transparent;")  # Şeffaf arka plan
            else:
                self.pet_label.setStyleSheet("background: none;")  # Normal arka plan

            self.pet_movie.start()

            # GIF'in tamamen yüklenmesi için 'finished' sinyali
            self.pet_movie.finished.connect(self.on_movie_finished)

            # GIF'in boyutunu QLabel'e göre ayarlama
            self.adjust_pet_size()

            # Pet'i doğru konumda göster
            self.pet_label.move(pet_info['x'], pet_info['y'])  # Son kaydedilen konum
            self.pet_label.show()

    def adjust_pet_size(self):
        """GIF boyutunu QLabel'e göre ayarlayın."""
        if self.pet_movie:
            # GIF'in boyutunu dinamik olarak ayarla
            image_size = self.pet_movie.currentImage().size()
            self.pet_label.resize(image_size)

    def on_movie_finished(self):
        """GIF tamamen yüklendiğinde yapılacak işlem."""
        # Pet'in son konumunu kaydedelim
        pet_name = self.pet_label.movie().fileName().split("/")[-1]
        pet_info = self.pet_data.get(pet_name, {})
        if pet_info:
            pet_info['x'], pet_info['y'] = self.pet_label.pos().x(), self.pet_label.pos().y()
            self.save_pet_data()

    def load_pet_list(self):
        """Pet listesini yükle."""
        self.pet_list_widget.clear()
        for pet_name, pet_info in self.pet_data.items():
            pet_item = QListWidgetItem()
            pet_item.setText(pet_name)  # Pet ismi burada gösterilecek

            # GIF'i küçük bir şekilde göstermek için QPixmap -> QIcon dönüşümü
            pixmap = QPixmap(pet_info['file']).scaled(100, 100)
            pet_item.setIcon(QIcon(pixmap))  # QPixmap'i QIcon'a çeviriyoruz

            self.pet_list_widget.addItem(pet_item)

    def show_pet(self):
        """Pet eklenince ekranda göster."""
        self.dragging = False
        self.drag_position = QPoint()

        # Son konumu yükle
        self.load_last_position()

    def closeEvent(self, event):
        """Uygulama kapanmadan önce son konumu kaydet."""
        self.save_position()
        event.accept()

    def save_position(self):
        """Pet'in son konumunu bir dosyaya kaydeder."""
        if self.pet_label:
            pet_name = self.pet_label.movie().fileName().split("/")[-1]
            pet_info = self.pet_data.get(pet_name, {})
            if pet_info:
                pet_info['x'], pet_info['y'] = self.pet_label.pos().x(), self.pet_label.pos().y()
                self.save_pet_data()

    def load_last_position(self):
        """Kaydedilen son konumu yükler."""
        # Son pet konumunu yükleme işlemi pet_data'dan yapılır
        pass

    def save_pet_data(self):
        """Pet verilerini dosyaya kaydeder."""
        # Pet verilerini gizli bir şekilde kaydedelim
        pet_data_path = os.path.join(os.getenv('APPDATA'), 'pet_data.json')
        with open(pet_data_path, "w") as file:
            json.dump(self.pet_data, file)

    def load_pet_data(self):
        """Pet verilerini dosyadan yükler."""
        pet_data_path = os.path.join(os.getenv('APPDATA'), 'pet_data.json')
        if os.path.exists(pet_data_path):
            with open(pet_data_path, "r") as file:
                return json.load(file)
        return {}

if __name__ == "__main__":
    app = QApplication(sys.argv)

    pet_app = DesktopPet()
    pet_app.show()

    sys.exit(app.exec_())
