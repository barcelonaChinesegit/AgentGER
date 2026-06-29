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
    <div className="rounded-xl border border-stone-200 bg-white/90 p-5 shadow-panel">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-brand-500">Input Figure</p>
          <h3 className="mt-1 text-lg font-bold text-stone-950">Upload chart image</h3>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
      </div>

      <div
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative min-h-[22rem] cursor-pointer rounded-xl border-2 transition-all duration-300
          ${isDragging 
            ? 'scale-[1.01] border-brand-400 bg-brand-50'
            : 'border-stone-200 bg-stone-50/70 hover:border-brand-300 hover:bg-brand-50/40'
          }
          ${uploadedImage ? 'border-solid' : 'border-dashed'}
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
          <div className="group relative h-full">
            <img
              src={uploadedImage.url}
              alt="已上传的图表"
              className="h-[22rem] w-full rounded-[10px] bg-white object-contain p-3"
            />
            <div className="absolute inset-0 flex items-center justify-center rounded-[10px] bg-stone-950/55 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
              <div className="text-center">
                <svg className="mx-auto mb-2 h-10 w-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span className="text-sm font-semibold text-white">点击更换图片</span>
              </div>
            </div>
            <div className="absolute bottom-3 left-3 right-3 rounded-lg border border-stone-200 bg-white/92 px-3 py-2 shadow-sm backdrop-blur-sm">
              <p className="truncate text-xs font-semibold text-stone-600">{uploadedImage.originalName}</p>
            </div>
          </div>
        ) : (
          <div className="flex min-h-[22rem] flex-col items-center justify-center px-6 py-14 text-center">
            <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-brand-50 text-brand-500 shadow-inner">
              <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <p className="mb-1 text-base font-bold text-stone-950">拖拽图片到这里</p>
            <p className="text-sm text-stone-500">或点击选择文件</p>
            <p className="mt-4 rounded-full bg-white px-3 py-1 text-xs font-medium text-stone-400 shadow-sm">
              PNG, JPG, GIF, WebP
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
