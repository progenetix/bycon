import Select, { createFilter, components } from "react-select"
import { FixedSizeList as List } from "react-window"
import cn from "classnames"
import React from "react"

export default function CustomSelect({
  value,
  onChange,
  options,
  className,
  useWindowList = true, // Required for big list for performance reasons
  ...selectProps
}) {
  const components =
    useWindowList && options?.length > 100
      ? { MenuList: WindowMenuList, Option }
      : { Option }
  return (
    <Select
      filterOption={createFilter({ ignoreAccents: false })} // MUCH faster
      components={components}
      options={options ?? []}
      value={value}
      onChange={onChange}
      className={cn(className, "react-select-container")}
      classNamePrefix="react-select"
      {...selectProps}
    />
  )
}

const height = 35

// GREATLY improves performances
function WindowMenuList(props) {
  const { options, children, maxHeight, getValue } = props
  const [value] = getValue()
  const initialOffset = options.indexOf(value) * height
  return (
    <List
      height={maxHeight}
      itemCount={children.length}
      itemSize={height}
      initialScrollOffset={initialOffset}
    >
      {({ index, style }) => <div style={style}>{children[index]}</div>}
    </List>
  )
}

function Option(props) {
  const { innerProps, isFocused, ...otherProps } = props
  const { onMouseMove, onMouseOver, ...otherInnerProps } = innerProps
  const newProps = { innerProps: { ...otherInnerProps }, ...otherProps }
  return (
    <components.Option {...newProps} className="react-select__option">
      {props.children}
    </components.Option>
  )
}
