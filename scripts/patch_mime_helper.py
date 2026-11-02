"""
scripts/patch_mime_helper.py — Adds robust isVideoFile / isImageFile helpers to MonitoringPage.tsx
"""
target_path = "frontend/src/pages/MonitoringPage.tsx"
with open(target_path, "r", encoding="utf-8") as f:
    content = f.read()

helpers = """  const isVideoFile = (f: File | null) => {
    if (!f) return false
    if (f.type && f.type.startsWith('video/')) return true
    const name = f.name.toLowerCase()
    return name.endsWith('.mp4') || name.endsWith('.avi') || name.endsWith('.webm') || name.endsWith('.mov') || name.endsWith('.mkv')
  }

  const isImageFile = (f: File | null) => {
    if (!f) return false
    if (f.type && f.type.startsWith('image/')) return true
    const name = f.name.toLowerCase()
    return name.endsWith('.jpg') || name.endsWith('.jpeg') || name.endsWith('.png') || name.endsWith('.webp') || name.endsWith('.bmp')
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {"""

content = content.replace("  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {", helpers, 1)

# In activeDetections
content = content.replace("    if (selectedFile?.type.startsWith('video/')) {", "    if (isVideoFile(selectedFile)) {", 1)

# In handleFileChange
old_file_change = """      if (file.type.startsWith('image/') || file.type.startsWith('video/')) {
        const url = URL.createObjectURL(file)
        setPreviewUrl(url)
        if (file.type.startsWith('video/')) {"""

new_file_change = """      if (isImageFile(file) || isVideoFile(file)) {
        const url = URL.createObjectURL(file)
        setPreviewUrl(url)
        if (isVideoFile(file)) {"""

content = content.replace(old_file_change, new_file_change, 1)

# In handleRunInference
content = content.replace("      if (selectedFile.type.startsWith('video/')) {", "      if (isVideoFile(selectedFile)) {", 1)

# In JSX
content = content.replace("                    {selectedFile?.type.startsWith('video/') ? (", "                    {isVideoFile(selectedFile) ? (", 1)

with open(target_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("MIME helpers patched successfully!")

