import React, { useState, useEffect } from 'react';

/**
 * Card Debug Panel Component - Phase 2.2 Implementation
 * Provides simple debugging information for flashcards
 */
function CardDebugPanel({ elementId, learningSetId, onFixStatus }) {
    const [debugData, setDebugData] = useState(null);
    const [showDebug, setShowDebug] = useState(false);
    const [loading, setLoading] = useState(false);
    const [fixing, setFixing] = useState(false);

    const fetchDebugData = async () => {
        if (!elementId) return;
        
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (learningSetId) params.append('learning_set_id', learningSetId);
            
            const response = await fetch(
                `/api/sessions/cards/${elementId}/debug?${params.toString()}`, 
                {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                }
            );
            
            if (response.ok) {
                const data = await response.json();
                setDebugData(data);
            } else {
                console.error('Debug fetch failed:', response.status);
            }
        } catch (error) {
            console.error('Debug fetch error:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleFixStatus = async () => {
        if (!elementId || fixing) return;
        
        setFixing(true);
        try {
            const params = new URLSearchParams();
            if (learningSetId) params.append('learning_set_id', learningSetId);
            
            const response = await fetch(
                `/api/sessions/cards/${elementId}/fix-status?${params.toString()}`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Content-Type': 'application/json'
                    }
                }
            );
            
            if (response.ok) {
                const result = await response.json();
                console.log('Status fix result:', result);
                
                // Refresh debug data
                await fetchDebugData();
                
                // Call parent callback if provided
                if (onFixStatus) {
                    onFixStatus(elementId, result);
                }
            } else {
                console.error('Status fix failed:', response.status);
            }
        } catch (error) {
            console.error('Status fix error:', error);
        } finally {
            setFixing(false);
        }
    };

    useEffect(() => {
        if (showDebug && !debugData && elementId) {
            fetchDebugData();
        }
    }, [showDebug, elementId]);

    if (!showDebug) {
        return (
            <button 
                onClick={() => setShowDebug(true)}
                className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 border border-gray-300 rounded transition-colors"
                title="Show debug information for this card"
            >
                🔍 Debug
            </button>
        );
    }

    return (
        <div className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded text-sm">
            <div className="flex justify-between items-center mb-3">
                <span className="font-semibold text-gray-700">Debug Information</span>
                <button 
                    onClick={() => setShowDebug(false)}
                    className="text-gray-500 hover:text-gray-700 text-lg leading-none"
                    title="Close debug panel"
                >
                    ✕
                </button>
            </div>

            {loading && (
                <div className="text-center py-4 text-gray-500">
                    Loading debug data...
                </div>
            )}

            {debugData && (
                <div className="space-y-3">
                    {/* Status Summary */}
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="text-xs font-medium text-gray-600 block mb-1">Stored Status</label>
                            <div className={`p-2 rounded text-xs font-medium ${
                                debugData.status_consistent 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-red-100 text-red-800'
                            }`}>
                                {debugData.stored_status || 'none'}
                                {!debugData.status_consistent && ' ⚠️'}
                            </div>
                        </div>
                        <div>
                            <label className="text-xs font-medium text-gray-600 block mb-1">Computed Status</label>
                            <div className="p-2 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                                {debugData.computed_status}
                            </div>
                        </div>
                    </div>

                    {/* Attempts Analysis */}
                    <div>
                        <label className="text-xs font-medium text-gray-600 block mb-1">Attempts Analysis</label>
                        <div className="p-2 bg-white border rounded">
                            <div className="grid grid-cols-3 gap-2 text-xs">
                                <span><strong>Total:</strong> {debugData.attempts_summary.total}</span>
                                <span><strong>Correct:</strong> {debugData.attempts_summary.correct}</span>
                                <span><strong>Accuracy:</strong> {(debugData.attempts_summary.accuracy * 100).toFixed(1)}%</span>
                            </div>
                            <div className="text-xs mt-2">
                                <strong>Success Streak:</strong> {debugData.attempts_summary.success_streak}
                            </div>
                            {debugData.attempts_summary.recent_pattern.length > 0 && (
                                <div className="text-xs mt-1">
                                    <strong>Recent Pattern:</strong> 
                                    <span className="ml-1 font-mono">
                                        {debugData.attempts_summary.recent_pattern.map((correct, idx) => 
                                            <span key={idx} className={correct ? 'text-green-600' : 'text-red-600'}>
                                                {correct ? '✓' : '✗'}
                                            </span>
                                        )}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Issues */}
                    {debugData.issues.length > 0 && (
                        <div>
                            <label className="text-xs font-medium text-gray-600 block mb-1">Issues Detected</label>
                            <div className="space-y-1">
                                {debugData.issues.map((issue, idx) => (
                                    <div key={idx} className="p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
                                        <div className="font-medium text-yellow-800">{issue.type.replace('_', ' ').toUpperCase()}</div>
                                        <div className="text-yellow-700">{issue.message}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Quick Actions */}
                    <div className="flex gap-2 pt-2 border-t border-gray-200">
                        <button 
                            onClick={fetchDebugData}
                            disabled={loading}
                            className="px-2 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 disabled:opacity-50"
                        >
                            🔄 Refresh
                        </button>
                        
                        {!debugData.status_consistent && (
                            <button 
                                onClick={handleFixStatus}
                                disabled={fixing}
                                className="px-2 py-1 bg-yellow-500 text-white text-xs rounded hover:bg-yellow-600 disabled:opacity-50"
                            >
                                {fixing ? '...' : '🔧 Fix Status'}
                            </button>
                        )}
                    </div>

                    {/* Metadata */}
                    <div className="text-xs text-gray-500 pt-2 border-t border-gray-200">
                        Element ID: {debugData.element_id}<br/>
                        Last Updated: {debugData.timestamps.review_updated ? 
                            new Date(debugData.timestamps.review_updated).toLocaleString() : 'Never'}
                    </div>
                </div>
            )}
        </div>
    );
}

export default CardDebugPanel;
