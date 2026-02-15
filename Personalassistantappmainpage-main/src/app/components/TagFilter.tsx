import { useState } from 'react';
import { Tag, Plus, X, Check } from 'lucide-react';

interface TagFilterProps {
    availableTags: string[];
    selectedTags: string[];
    onTagToggle: (tag: string) => void;
    onAddTag?: (tag: string) => void;
}

export function TagFilter({ availableTags, selectedTags, onTagToggle, onAddTag }: TagFilterProps) {
    const [isAddingTag, setIsAddingTag] = useState(false);
    const [newTagName, setNewTagName] = useState('');

    const handleAddTag = () => {
        if (newTagName.trim() && onAddTag) {
            onAddTag(newTagName.trim());
            setNewTagName('');
            setIsAddingTag(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleAddTag();
        } else if (e.key === 'Escape') {
            setIsAddingTag(false);
            setNewTagName('');
        }
    };

    return (
        <div className="space-y-3">
            {/* Tag chips for filtering */}
            <div className="flex flex-wrap gap-2">
                <button
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${selectedTags.length === 0
                        ? 'bg-[#2774AE]/30 text-[#FFD100] border border-[#2774AE]'
                        : 'bg-white/5 text-gray-400 hover:bg-white/10 border border-transparent'
                        }`}
                    onClick={() => selectedTags.forEach(tag => onTagToggle(tag))}
                >
                    <Tag className="w-3.5 h-3.5" />
                    All
                </button>

                {availableTags.map((tag) => {
                    const isSelected = selectedTags.includes(tag);
                    return (
                        <button
                            key={tag}
                            onClick={() => onTagToggle(tag)}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${isSelected
                                ? 'bg-[#2774AE]/30 text-[#FFD100] border border-[#2774AE]'
                                : 'bg-white/5 text-gray-400 hover:bg-white/10 border border-transparent'
                                }`}
                        >
                            {isSelected && <Check className="w-3.5 h-3.5" />}
                            {tag}
                        </button>
                    );
                })}
            </div>

            {/* Add new tag */}
            {onAddTag && (
                <div className="flex items-center gap-2">
                    {isAddingTag ? (
                        <div className="flex items-center gap-2">
                            <input
                                type="text"
                                value={newTagName}
                                onChange={(e) => setNewTagName(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Tag name..."
                                autoFocus
                                className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#2774AE]"
                            />
                            <button
                                onClick={handleAddTag}
                                disabled={!newTagName.trim()}
                                className="p-1.5 rounded-lg bg-[#2774AE] hover:bg-[#1e5f8e] text-white disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Check className="w-4 h-4" />
                            </button>
                            <button
                                onClick={() => { setIsAddingTag(false); setNewTagName(''); }}
                                className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-gray-400"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                    ) : (
                        <button
                            onClick={() => setIsAddingTag(true)}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-400 hover:text-white transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                            New tag
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}

// Sidebar tag list for the left navigation
interface TagSidebarProps {
    tags: string[];
    selectedTag: string | null;
    onTagSelect: (tag: string | null) => void;
    onAddTag?: (tag: string) => void;
}

export function TagSidebar({ tags, selectedTag, onTagSelect, onAddTag }: TagSidebarProps) {
    const [isAddingTag, setIsAddingTag] = useState(false);
    const [newTagName, setNewTagName] = useState('');

    const handleAddTag = () => {
        if (newTagName.trim() && onAddTag) {
            onAddTag(newTagName.trim());
            setNewTagName('');
            setIsAddingTag(false);
        }
    };

    const tagColors: { [key: string]: string } = {
        'Follow-up': 'bg-[#2774AE]',
        'Important': 'bg-red-500',
        'Meeting Notes': 'bg-blue-500',
        'Work': 'bg-green-500',
        'Personal': 'bg-yellow-500',
    };

    const getTagColor = (tag: string) => {
        return tagColors[tag] || 'bg-gray-500';
    };

    return (
        <div className="space-y-1">
            <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tags
            </div>

            {tags.map((tag) => (
                <button
                    key={tag}
                    onClick={() => onTagSelect(selectedTag === tag ? null : tag)}
                    className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${selectedTag === tag
                        ? 'bg-white/10 text-white'
                        : 'text-gray-400 hover:bg-white/5 hover:text-white'
                        }`}
                >
                    <div className={`w-2 h-2 rounded-full ${getTagColor(tag)}`} />
                    {tag}
                </button>
            ))}

            {/* Add new tag */}
            {isAddingTag ? (
                <div className="px-3 py-2">
                    <input
                        type="text"
                        value={newTagName}
                        onChange={(e) => setNewTagName(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') handleAddTag();
                            if (e.key === 'Escape') { setIsAddingTag(false); setNewTagName(''); }
                        }}
                        placeholder="New tag..."
                        autoFocus
                        className="w-full px-2 py-1 bg-white/5 border border-white/10 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#2774AE]"
                    />
                </div>
            ) : (
                <button
                    onClick={() => setIsAddingTag(true)}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                >
                    <Plus className="w-4 h-4" />
                    New tag
                </button>
            )}
        </div>
    );
}
