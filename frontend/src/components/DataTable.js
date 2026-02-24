import React from "react";

function DataTable({ data, selectedRows = [], onToggleRow, onToggleAll, onSelectAll, onDeselectAll, onExport, exporting = false }) {
  if (!data || data.length === 0) {
    return null;
  }

  const allSelected = selectedRows.length === data.length;
  const someSelected = selectedRows.length > 0 && !allSelected;

  // Get all unique keys from the data
  const columns = [
    "date",
    "heading",
    "input_summary",
    "fmn",
    "aor_lower_fmn",
    "unit",
    "agency",
    "country",
    "state",
    "district",
    "gen_area",
    "gp",
    "coordinates",
    "engagement_type_reasoned",
    "cadres_min",
    "cadres_max",
    "leader",
    "weapons",
    "ammunition"
  ];

  // Column headers mapping
  const columnHeaders = {
    date: "Date",
    heading: "Heading",
    input_summary: "Summary",
    fmn: "FMN",
    aor_lower_fmn: "AOR Lower FMN",
    unit: "Unit",
    agency: "Agency",
    country: "Country",
    state: "State",
    district: "District",
    gen_area: "General Area",
    gp: "Group/Faction",
    coordinates: "Coordinates",
    engagement_type_reasoned: "Engagement Type",
    cadres_min: "Cadres Min",
    cadres_max: "Cadres Max",
    leader: "Leader",
    weapons: "Weapons",
    ammunition: "Ammunition"
  };

  // Calculate max length for each column to determine if it needs more width
  const getColumnMaxLength = (col) => {
    if (!data || data.length === 0) return 0;
    return Math.max(...data.map(row => {
      const val = row[col];
      return val ? String(val).length : 0;
    }));
  };

  // Determine column CSS class based on content and type
  const getColumnClass = (col) => {
    const classes = ['table-cell'];
    const maxLength = getColumnMaxLength(col);
    
    // Summary gets 5x width
    if (col === 'input_summary') {
      classes.push('col-summary');
    }
    // Auto-adjust for all other columns based on content length
    // Long content (>100 chars)
    else if (maxLength > 100) {
      classes.push('col-long');
    }
    // Medium length (50-100 chars)
    else if (maxLength > 50) {
      classes.push('col-medium');
    }
    // Short content
    else {
      classes.push('col-short');
    }
    
    return classes.join(' ');
  };

  return (
    <div className="data-table-container">
      <div className="table-header">
        <h3 className="table-title">📊 Extracted Records ({data.length})</h3>
        <p className="table-description">
          Below are the intelligence records extracted from your PDF
        </p>
      </div>

      {/* Export Controls */}
      <div className="export-controls">
        <div className="selection-buttons">
          <button
            className="btn btn-text"
            onClick={onSelectAll}
            disabled={exporting || allSelected}
          >
            Select All
          </button>
          <button
            className="btn btn-text"
            onClick={onDeselectAll}
            disabled={exporting || selectedRows.length === 0}
          >
            Deselect All
          </button>
        </div>
        
        <button
          className="btn btn-export"
          onClick={onExport}
          disabled={exporting || data.length === 0}
        >
          {exporting ? (
            <>
              <span className="spinner-small"></span>
              Exporting...
            </>
          ) : (
            <>
              📥 {selectedRows.length > 0 
                ? `Export Selected (${selectedRows.length})` 
                : `Export All (${data.length})`}
            </>
          )}
        </button>
      </div>
      
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th className="row-checkbox">
                <input
                  type="checkbox"
                  checked={allSelected}
                  ref={(input) => {
                    if (input) input.indeterminate = someSelected;
                  }}
                  onChange={() => onToggleAll(data)}
                  title={allSelected ? "Deselect all" : "Select all"}
                />
              </th>
              <th className="row-number">#</th>
              {columns.map((col) => (
                <th key={col} className={getColumnClass(col)}>
                  {columnHeaders[col]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => {
              const isSelected = selectedRows.includes(index);
              return (
                <tr key={index} className={isSelected ? "selected-row" : ""}>
                  <td className="row-checkbox">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => onToggleRow(index)}
                    />
                  </td>
                  <td className="row-number">{index + 1}</td>
                  {columns.map((col) => (
                    <td key={col} className={getColumnClass(col)}>
                      {row[col] !== null && row[col] !== undefined && row[col] !== ""
                        ? String(row[col])
                        : "-"}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default DataTable;
