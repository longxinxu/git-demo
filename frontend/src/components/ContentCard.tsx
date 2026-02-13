import type { ContentItem } from '../types/api';

export function ContentCard({ item, onFavorite }: { item: ContentItem; onFavorite?: (id: number) => void }) {
  return (
    <article style={{ border: '1px solid #ddd', padding: 12, marginBottom: 8 }}>
      <div>{item.category} · {item.status}</div>
      <h3>{item.title}</h3>
      <p>{item.summary}</p>
      <small>质量分: {item.quality_score}</small>
      {onFavorite && <button onClick={() => onFavorite(item.id)}>收藏</button>}
    </article>
  );
}
