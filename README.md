# 🌙 Improving Illumination in Night Time Images  

This project enhances **nighttime images** by improving **visibility, contrast, and reducing noise** using advanced image processing techniques. The algorithm leverages **Guided Image Filtering** and **Atmospheric Light Estimation** to restore low-light images effectively.  

## 🧩 Features  
- 🌃 **Enhances dark images** by improving brightness and contrast.  
- 🔍 **Preserves important image details** while reducing noise.  
- 🎨 **Utilizes image dehazing techniques** for clarity improvement.  
- ⚡ **Fast processing** with OpenCV and NumPy.  

## ⚙️ Requirements  
Make sure you have the following dependencies installed:  

```sh
pip install opencv-python numpy
```

- 🐍 Python 3.x  
- 📷 OpenCV (`cv2`)  
- 🔢 NumPy  

## 🚀 Usage  
To run the program, execute:  

```sh
python Improving_Illumination.py
```  

### Steps:  
1. **📂 Select an image** using the file dialog.  
2. The script processes and displays:  
   - 🏞️ **Original Image**  
   - ✨ **Enhanced Image Versions**  
3. **Close the windows** when done.  

## 🏗️ Architecture  
![Architecture](./assets/architecture.png)  

## 🔧 Schematic  
![Schematic](./assets/schematic.png)  

## 🧠 Logic Flow  
![Logic Flow](./assets/logic.png)  

## 📊 Example Output  
### 🖼️ Original vs. Enhanced Image  
Original Image | Enhanced Image  
--- | ---  
![Original](./assets/original.jpg) | ![Enhanced](./assets/enhanced.jpg)  

## 📁 Project Structure  
```
📂 Improving_Illumination/
├── 📜 Improving_Illumination.py  # Main script
├── 📂 assets/                    # Image assets
│   ├── original.jpg              # Sample input
│   ├── enhanced.jpg              # Sample output
└── 📜 README.md                  # Documentation
```

## 🙏 Acknowledgments  
This project is inspired by **low-light enhancement** and **image dehazing techniques** used in computer vision research.  
