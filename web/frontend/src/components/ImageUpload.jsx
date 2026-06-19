import { useState, useRef } from 'react';

export default function ImageUpload({ onUpload, uploadedImage, isLoading }) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileSelect = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFile = (file) => {
    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件');
      return;
    }
    onUpload(file);
  };

  const handleClick = () => {
    if (!isLoading) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
        <svg className="w-4 h-4 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        上传图表
      </label>

      <div
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative cursor-pointer rounded-xl transition-all duration-300
          ${isDragging 
            ? 'border-brand-400 bg-brand-500/10 scale-[1.02]' 
            : 'border-slate-600 hover:border-brand-500/50 hover:bg-slate-800/30'
          }
          ${uploadedImage ? 'border-solid border-2' : 'border-dashed border-2'}
          ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
          disabled={isLoading}
        />

        {uploadedImage ? (
          <div className="relative group">
            <img
              src={uploadedImage.url}
              alt="已上传的图表"
              className="w-full h-64 object-contain rounded-xl bg-slate-900/50"
            />
            <div className="absolute inset-0 bg-slate-900/80 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl flex items-center justify-center">
              <div className="text-center">
                <svg className="w-10 h-10 mx-auto text-brand-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span className="text-slate-300 text-sm">点击更换图片</span>
              </div>
            </div>
            <div className="absolute bottom-2 left-2 right-2 bg-slate-900/90 backdrop-blur-sm rounded-lg px-3 py-1.5">
              <p className="text-xs text-slate-400 truncate">{uploadedImage.originalName}</p>
            </div>
          </div>
        ) : (
          <div className="py-16 px-6 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-brand-500/20 to-brand-600/10 mb-4">
              <svg className="w-8 h-8 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <p className="text-slate-300 font-medium mb-1">拖拽图片到这里</p>
            <p className="text-slate-500 text-sm">或点击选择文件</p>
            <p className="text-slate-600 text-xs mt-3">支持 PNG, JPG, GIF, WebP</p>
          </div>
        )}
      </div>
    </div>
  );
}

