/**
 * DDAnalysis Component
 * Displays Double Dummy Analysis results in a formatted table
 */

function DDAnalysis({ ddAnalysis }) {
    if (!ddAnalysis) {
        return (
            <div className="text-gray-500 text-sm italic">
                No double dummy analysis available yet
            </div>
        );
    }

    const renderTable = () => {
        try {
            const data = typeof ddAnalysis === 'string' 
                ? JSON.parse(ddAnalysis) 
                : ddAnalysis;

            if (data.table) {
                return (
                    <div className="overflow-x-auto">
                        <table className="w-full text-xs border-collapse">
                            <thead>
                                <tr className="bg-gray-700">
                                    <th className="border border-gray-600 px-2 py-1">Player</th>
                                    <th className="border border-gray-600 px-2 py-1">♠</th>
                                    <th className="border border-gray-600 px-2 py-1">♥</th>
                                    <th className="border border-gray-600 px-2 py-1">♦</th>
                                    <th className="border border-gray-600 px-2 py-1">♣</th>
                                    <th className="border border-gray-600 px-2 py-1">NT</th>
                                </tr>
                            </thead>
                            <tbody>
                                {Object.entries(data.table).map(([player, tricks]) => (
                                    <tr key={player} className="hover:bg-gray-700/50">
                                        <td className="border border-gray-600 px-2 py-1 font-semibold">
                                            {player}
                                        </td>
                                        {['S', 'H', 'D', 'C', 'NT'].map(suit => (
                                            <td 
                                                key={suit}
                                                className="border border-gray-600 px-2 py-1 text-center"
                                            >
                                                {tricks[suit] !== undefined ? tricks[suit] : '-'}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                );
            }

            return (
                <div className="text-sm font-mono whitespace-pre-wrap">
                    {JSON.stringify(data, null, 2)}
                </div>
            );
        } catch (e) {
            return (
                <div className="text-sm font-mono whitespace-pre-wrap">
                    {ddAnalysis}
                </div>
            );
        }
    };

    return (
        <div className="bg-gray-800/95 rounded-lg p-3 border border-gray-700 backdrop-blur-sm">
            <h3 className="text-sm font-semibold mb-2 text-gray-300">
                Double Dummy Analysis
            </h3>
            {renderTable()}
        </div>
    );
}
