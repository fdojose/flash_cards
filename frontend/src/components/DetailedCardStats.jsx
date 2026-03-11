import { useState, useEffect, useRef } from 'react';
import { useDetailedCardStats } from '../hooks/useApi';

const StatusBadge = ({ status }) => {
  const statusConfig = {
    'learning': { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Learning' },
    'isolation_mastered': { bg: 'bg-green-100', text: 'text-green-800', label: 'Isolated' },
    'integration_review': { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Integration' },
    'integration_confirmed': { bg: 'bg-purple-100', text: 'text-purple-800', label: 'Confirmed' },
    'spiral_review': { bg: 'bg-indigo-100', text: 'text-indigo-800', label: 'Spiral' },
    'not_started': { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Not Started' }
  };
  
  const config = statusConfig[status] || statusConfig['not_started'];
  
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
};

const AttemptCell = ({ correct, incorrect, total }) => {
  if (total === 0) return <span className="text-gray-400">-</span>;
  
  const accuracy = correct / total;
  const accuracyColor = accuracy >= 0.8 ? 'text-green-600' : accuracy >= 0.6 ? 'text-yellow-600' : 'text-red-600';
  
  return (
    <div className="text-sm">
      <div className="font-medium">
        <span className="text-green-600">{correct}</span>/
        <span className="text-red-600">{incorrect}</span>
      </div>
      <div className={`text-xs ${accuracyColor}`}>
        {Math.round(accuracy * 100)}%
      </div>
    </div>
  );
};

export default function DetailedCardStats({ learningSetId }) {
  const { stats, loading, error, refetch } = useDetailedCardStats(learningSetId);
  const [isExpanded, setIsExpanded] = useState(false);
  const [sortBy, setSortBy] = useState('total_attempts');
  const [sortOrder, setSortOrder] = useState('desc');
  const containerRef = useRef(null);

  useEffect(() => {
    if (learningSetId && containerRef.current) {
      containerRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setIsExpanded(true);
    }
  }, [learningSetId]);

  if (!learningSetId) {
    return (
      <div ref={containerRef} className="card-flashcard p-6">
        <h3 className="text-lg font-semibold mb-4">📊 Detailed Card Statistics</h3>
        <p className="text-gray-600">Select a learning set to view detailed statistics.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div ref={containerRef} className="card-flashcard p-6">
        <h3 className="text-lg font-semibold mb-4">📊 Detailed Card Statistics</h3>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading detailed statistics...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div ref={containerRef} className="card-flashcard p-6">
        <h3 className="text-lg font-semibold mb-4">📊 Detailed Card Statistics</h3>
        <div className="text-center py-8">
          <div className="text-red-500 mb-2">⚠️ Failed to load statistics</div>
          <button 
            onClick={refetch}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!stats || !stats.cards) {
    return (
      <div ref={containerRef} className="card-flashcard p-6">
        <h3 className="text-lg font-semibold mb-4">📊 Detailed Card Statistics</h3>
        <p className="text-gray-600">No statistics available for this learning set.</p>
      </div>
    );
  }

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const sortedCards = [...stats.cards].sort((a, b) => {
    let aVal, bVal;
    
    switch (sortBy) {
      case 'content':
        aVal = a.element_content.toLowerCase();
        bVal = b.element_content.toLowerCase();
        break;
      case 'status':
        aVal = a.current_status;
        bVal = b.current_status;
        break;
      case 'accuracy':
        aVal = a.overall_accuracy;
        bVal = b.overall_accuracy;
        break;
      default:
        aVal = a[sortBy];
        bVal = b[sortBy];
    }
    
    if (sortOrder === 'asc') {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });

  return (
    <div ref={containerRef} className="card-flashcard p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">📊 Detailed Card Statistics</h3>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded hover:bg-blue-200 transition-colors"
        >
          {isExpanded ? 'Hide Details' : 'Show Details'}
        </button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">{stats.summary.total_cards}</div>
          <div className="text-sm text-gray-600">Total Cards</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{stats.summary.cards_with_attempts}</div>
          <div className="text-sm text-gray-600">Cards Practiced</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">{stats.summary.average_attempts_per_card}</div>
          <div className="text-sm text-gray-600">Avg Attempts</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600">
            {Object.keys(stats.summary.status_distribution).length}
          </div>
          <div className="text-sm text-gray-600">Status Types</div>
        </div>
      </div>

      {/* Status Distribution */}
      <div className="mb-6">
        <h4 className="font-medium mb-2">Status Distribution</h4>
        <div className="flex flex-wrap gap-2">
          {Object.entries(stats.summary.status_distribution).map(([status, count]) => (
            <div key={status} className="flex items-center space-x-2">
              <StatusBadge status={status} />
              <span className="text-sm text-gray-600">({count})</span>
            </div>
          ))}
        </div>
      </div>

      {isExpanded && (
        <>
          {/* Controls */}
          <div className="flex items-center space-x-4 mb-4">
            <span className="text-sm text-gray-600">Sort by:</span>
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
              className="text-sm border rounded px-2 py-1"
            >
              <option value="total_attempts">Total Attempts</option>
              <option value="overall_accuracy">Accuracy</option>
              <option value="current_status">Status</option>
              <option value="element_content">Content</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="text-sm px-2 py-1 border rounded hover:bg-gray-50"
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </button>
            <button
              onClick={refetch}
              className="text-sm px-3 py-1 bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
            >
              🔄 Refresh
            </button>
          </div>

          {/* Detailed Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left p-3 cursor-pointer hover:bg-gray-100" onClick={() => handleSort('element_content')}>
                    Card Content {sortBy === 'element_content' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="text-left p-3 cursor-pointer hover:bg-gray-100" onClick={() => handleSort('current_status')}>
                    Status {sortBy === 'current_status' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="text-center p-3 cursor-pointer hover:bg-gray-100" onClick={() => handleSort('total_attempts')}>
                    Total {sortBy === 'total_attempts' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="text-center p-3 cursor-pointer hover:bg-gray-100" onClick={() => handleSort('overall_accuracy')}>
                    Overall {sortBy === 'overall_accuracy' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="text-center p-3">Learning</th>
                  <th className="text-center p-3">Isolated</th>
                  <th className="text-center p-3">Integration</th>
                  <th className="text-center p-3">Confirmed</th>
                  <th className="text-center p-3">Spiral</th>
                </tr>
              </thead>
              <tbody>
                {sortedCards.map((card, index) => (
                  <tr key={card.element_id} className={`border-b hover:bg-gray-50 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-25'}`}>
                    <td className="p-3 max-w-xs">
                      <div className="truncate" title={card.element_content}>
                        {card.element_content}
                      </div>
                    </td>
                    <td className="p-3">
                      <StatusBadge status={card.current_status} />
                    </td>
                    <td className="p-3 text-center">
                      <div className="font-medium">{card.total_attempts}</div>
                      <div className="text-xs text-gray-500">
                        {card.total_correct}/{card.total_attempts - card.total_correct}
                      </div>
                    </td>
                    <td className="p-3 text-center">
                      <div className={`font-medium ${card.overall_accuracy >= 0.8 ? 'text-green-600' : card.overall_accuracy >= 0.6 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {Math.round(card.overall_accuracy * 100)}%
                      </div>
                    </td>
                    <td className="p-3 text-center">
                      <AttemptCell {...card.stats_by_status.learning} />
                    </td>
                    <td className="p-3 text-center">
                      <AttemptCell {...card.stats_by_status.isolation_mastered} />
                    </td>
                    <td className="p-3 text-center">
                      <AttemptCell {...card.stats_by_status.integration_review} />
                    </td>
                    <td className="p-3 text-center">
                      <AttemptCell {...card.stats_by_status.integration_confirmed} />
                    </td>
                    <td className="p-3 text-center">
                      <AttemptCell {...card.stats_by_status.spiral_review} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {sortedCards.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No cards found in this learning set.
            </div>
          )}
        </>
      )}
    </div>
  );
}
