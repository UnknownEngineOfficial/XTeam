import React, { useState, useEffect, useRef } from 'react';
import { RefreshCw, ExternalLink, Smartphone, Tablet, Monitor } from 'lucide-react';
import Button from '../common/Button';

interface LivePreviewProps {
  html: string;
  css?: string;
  js?: string;
  className?: string;
}

type ViewportSize = 'mobile' | 'tablet' | 'desktop';

const LivePreview: React.FC<LivePreviewProps> = ({
  html,
  css = '',
  js = '',
  className = '',
}) => {
  const [viewport, setViewport] = useState<ViewportSize>('desktop');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const viewportSizes = {
    mobile: { width: 375, height: 667, icon: Smartphone },
    tablet: { width: 768, height: 1024, icon: Tablet },
    desktop: { width: '100%', height: '100%', icon: Monitor },
  };

  const generatePreviewContent = () => {
    const combinedHTML = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Live Preview</title>
        <style>
          ${css}
          /* Reset and base styles */
          * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
          }
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
          }
        </style>
      </head>
      <body>
        ${html}
        <script>
          ${js}
        </script>
      </body>
      </html>
    `;
    return combinedHTML;
  };

  const refreshPreview = () => {
    setIsRefreshing(true);
    if (iframeRef.current) {
      const content = generatePreviewContent();
      iframeRef.current.srcdoc = content;
    }
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const openInNewTab = () => {
    const content = generatePreviewContent();
    const blob = new Blob([content], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  };

  useEffect(() => {
    refreshPreview();
  }, [html, css, js]);

  const currentSize = viewportSizes[viewport];

  return (
    <div className={`flex flex-col h-full bg-white border border-gray-200 ${className}`}>
      {/* Preview Controls */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-2">
          <h3 className="text-sm font-medium text-gray-900">Live Preview</h3>
          <div className="flex items-center space-x-1">
            {Object.entries(viewportSizes).map(([key, size]) => {
              const ViewportIcon = size.icon;
              return (
                <Button
                  key={key}
                  variant={viewport === key ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setViewport(key as ViewportSize)}
                  className="p-1"
                  title={`${key.charAt(0).toUpperCase() + key.slice(1)} view`}
                >
                  <ViewportIcon className="w-4 h-4" />
                </Button>
              );
            })}
          </div>
        </div>

        <div className="flex items-center space-x-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={refreshPreview}
            disabled={isRefreshing}
            className="p-1"
            title="Refresh preview"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={openInNewTab}
            className="p-1"
            title="Open in new tab"
          >
            <ExternalLink className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Preview Content */}
      <div className="flex-1 bg-gray-100 p-4">
        <div
          className="mx-auto bg-white border border-gray-300 rounded-lg shadow-lg overflow-hidden"
          style={{
            width: typeof currentSize.width === 'number' ? `${currentSize.width}px` : currentSize.width,
            height: typeof currentSize.height === 'number' ? `${currentSize.height}px` : currentSize.height,
            maxWidth: '100%',
            maxHeight: '100%',
          }}
        >
          <iframe
            ref={iframeRef}
            className="w-full h-full border-0"
            title="Live Preview"
            sandbox="allow-scripts allow-same-origin"
          />
        </div>

        {/* Viewport Info */}
        <div className="mt-2 text-center text-xs text-gray-500">
          {viewport === 'desktop' ? (
            'Desktop View'
          ) : (
            `${viewport.charAt(0).toUpperCase() + viewport.slice(1)} (${currentSize.width}×${currentSize.height})`
          )}
        </div>
      </div>
    </div>
  );
};

export default LivePreview;
