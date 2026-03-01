// 增强版的adoptSuggestion函数
export function enhanceAdoptSuggestion(suggestion, htmlContent) {
  // 处理HTML标签相关的建议
  if (suggestion.explanation && (
      suggestion.explanation.includes("标签") || 
      suggestion.explanation.includes("HTML") ||
      suggestion.explanation.includes("<p>")
    )) {
    // 处理<p>标签之间的空行
    if (suggestion.explanation.includes("<p>") && suggestion.explanation.includes("空行")) {
      const regex = /(<p>.*?<\/p>)\s*(<p>)/gs;
      if (htmlContent.match(regex)) {
        return htmlContent.replace(regex, "$1$2");
      }
    } 
    // 处理其他HTML相关替换
    else if (suggestion.original && suggestion.suggested) {
      const escapedOriginal = suggestion.original.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const regex = new RegExp(escapedOriginal, "g");
      
      if (htmlContent.match(regex)) {
        return htmlContent.replace(regex, suggestion.suggested);
      }
    }
  }
  
  // 处理甲乙方表述
  if (suggestion.explanation) {
    // 处理甲方表述
    if (suggestion.explanation.includes("甲方")) {
      const regex = /甲\s*方[^。，；,;.]{0,30}/g;
      if (htmlContent.match(regex)) {
        return htmlContent.replace(regex, suggestion.suggested);
      }
    }
    // 处理乙方表述
    else if (suggestion.explanation.includes("乙方")) {
      const regex = /乙\s*方[^。，；,;.]{0,30}/g;
      if (htmlContent.match(regex)) {
        return htmlContent.replace(regex, suggestion.suggested);
      }
    }
  }
  
  // 如果没有特殊处理，返回null表示需要继续尝试其他方法
  return null;
}
