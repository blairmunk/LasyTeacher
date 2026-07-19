/**
 * Backward-compatible loader for the document rendering script.
 */
(function() {
    var currentScript = document.currentScript;
    if (!currentScript || !currentScript.src) return;

    var renderingScriptSrc = currentScript.src.replace(
        'document_generation.js',
        'document_rendering.js'
    );
    if (document.querySelector('script[src="' + renderingScriptSrc + '"]')) {
        return;
    }

    var script = document.createElement('script');
    script.src = renderingScriptSrc;
    document.head.appendChild(script);
})();
