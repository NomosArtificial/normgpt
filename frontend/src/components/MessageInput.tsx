import { useRef, useCallback } from "react";

interface Props {
  onSend: (content: string) => void;
  disabled: boolean;
}

export default function MessageInput({ onSend, disabled }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  const autoResize = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, []);

  const handleSend = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    const content = el.value.trim();
    if (!content) return;
    el.value = "";
    autoResize();
    onSend(content);
  }, [onSend, autoResize]);

  return (
    <div id="input-area">
      <div id="input-wrapper">
        <textarea
          ref={ref}
          id="msg-input"
          placeholder="Send a message..."
          rows={1}
          onInput={autoResize}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
        <button id="send-btn" disabled={disabled} onClick={handleSend}>
          Send
        </button>
      </div>
    </div>
  );
}
