import React, { useState } from 'react';

export function ShowJSON({ data }) {

  const [isOpened, setIsOpened] = useState(false);

  function toggle() {
    setIsOpened(wasOpened => !wasOpened);
  }

  return (
    <>
      <h5><span onClick={toggle}>Raw Data (click to show/hide)</span></h5>
        {isOpened && (
          <div>
            <pre className="prettyprint">{ JSON.stringify(data, null, 2) }</pre>
          </div>
        )}
    </>
  )
}
