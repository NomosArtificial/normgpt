interface StreamChunk {
  type: "text" | "done";
  content: string;
}

export async function processSSEStream(
  response: Response,
  onText: (chunk: string) => void,
  onDone: () => void,
): Promise<void> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });

    const lines = buf.split("\n");
    buf = lines.pop()!;

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const chunk: StreamChunk = JSON.parse(line.slice(6));

      if (chunk.type === "done") {
        onDone();
        return;
      }

      onText(chunk.content);
    }
  }

  onDone();
}
