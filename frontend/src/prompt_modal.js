import * as React from "react";
import PropTypes from "prop-types";
import { styled, css } from "@mui/system";
import { Modal as BaseModal, Grid, Select, MenuItem } from "@mui/material";
import Fade from "@mui/material/Fade";
import { Button, TextField } from "@mui/material";
import { API_URL } from "./constants";
import { getPrompts } from "./functions";

async function savePrompt(
  region,
  template,
  contextData,
  temperature,
  top_p,
  top_k,
  max_tokens,
  stop_sequences,
  showDialog,
  setDialogMsg,
  name,
  desc,
  modelId,
) {
  const transformedList = contextData
    .filter((item) => item.variable !== "")
    .map((item) => ({
      name: item.variable,
    }));

  const payload = {
    region: region,
    name: name,
    description: desc,
    prompt: template,
    inputs: transformedList,
    temperature: temperature,
    top_p: top_p,
    top_k: top_k,
    max_tokens: max_tokens,
    stop_sequences: stop_sequences,
    model_id: modelId,
  };

  const response = await fetch(API_URL + "/save_prompt", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (response.ok) {
    const data = await response.json();
    const url =
      "https://" +
      region +
      ".console.aws.amazon.com/bedrock/home?region=" +
      region +
      "#/prompt-management/" +
      data["id"];

    showDialog(true);
    setDialogMsg(
      <Button color="success" variant="contained" href={url} target="_blank">
        Prompt Template Saved!
      </Button>,
    );
  }

  if (!response.ok) {
    showDialog(true);
    setDialogMsg("Error occurred while saving prompt");
    console.log(response);
  }

  return "";
}

async function updatePrompt(
  region,
  template,
  contextData,
  temperature,
  top_p,
  top_k,
  max_tokens,
  stop_sequences,
  showDialog,
  setDialogMsg,
  name,
  desc,
  modelId,
  promptIdentifier,
) {
  const transformedList = contextData
    .filter((item) => item.variable !== "")
    .map((item) => ({
      name: item.variable,
    }));

  const payload = {
    region: region,
    name: name,
    description: desc,
    prompt: template,
    inputs: transformedList,
    temperature: temperature,
    top_p: top_p,
    top_k: top_k,
    max_tokens: max_tokens,
    stop_sequences: stop_sequences,
    model_id: modelId,
    prompt_identifier: promptIdentifier,
  };

  const response = await fetch(API_URL + "/update_prompt", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (response.ok) {
    const data = await response.json();
    const url =
      "https://" +
      region +
      ".console.aws.amazon.com/bedrock/home?region=" +
      region +
      "#/prompt-management/" +
      data["id"];
    showDialog(true);
    setDialogMsg(
      <Button color="success" variant="contained" href={url} target="_blank">
        Prompt Template Saved!
      </Button>,
    );
  }

  if (!response.ok) {
    showDialog(true);
    setDialogMsg("Error occurred while updating prompt");
    console.log(response);
  }

  return "";
}

const TransitionsModal = function TransitionsModal({
  region,
  template,
  contextData,
  temperature,
  top_p,
  top_k,
  max_tokens,
  stop_sequences,
  availableModels,
  modelMap,
  selectedPrompt,
  setSelectedPrompt,
  setSelectedPromptId,
  prompts,
  setPrompts,
  showDialog,
  setDialogMsg,
}) {
  const [open, setOpen] = React.useState(false);
  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);

  const [name, setName] = React.useState("");
  const [desc, setDesc] = React.useState("");

  const [model, setModel] = React.useState("");

  async function handleSavePrompt(event) {
    //check if this prompt exists already in our list
    const promptExisting = prompts.filter((prompt) => prompt.name === name);

    if (promptExisting.length > 0) {
      await updatePrompt(
        region,
        template,
        contextData,
        temperature,
        top_p,
        top_k,
        max_tokens,
        stop_sequences,
        showDialog,
        setDialogMsg,
        name,
        desc,
        modelMap[model],
        promptExisting[0]["id"],
      );
    } else {
      await savePrompt(
        region,
        template,
        contextData,
        temperature,
        top_p,
        top_k,
        max_tokens,
        stop_sequences,
        showDialog,
        setDialogMsg,
        name,
        desc,
        modelMap[model],
      );
    }

    const results = await getPrompts(
      region,
      setPrompts,
      setDialogMsg,
      showDialog,
    );
    setSelectedPrompt(name);
    const filteredPrompt = results.filter((item) => item.name === name);
    setSelectedPromptId(filteredPrompt[0]["id"]);
  }

  React.useEffect(() => {
    setName(selectedPrompt);
  }, [selectedPrompt]);

  return (
    <div>
      {/* <TriggerButton onClick={handleOpen}>Open modal</TriggerButton> */}
      <Button
        variant="contained"
        color="secondary"
        fullWidth
        style={{ marginTop: "10px" }}
        onClick={handleOpen}
      >
        Save
      </Button>
      <Modal
        aria-labelledby="transition-modal-title"
        aria-describedby="transition-modal-description"
        open={open}
        onClose={handleClose}
        closeAfterTransition
        slots={{ backdrop: StyledBackdrop }}
      >
        <Fade in={open}>
          <ModalContent sx={style}>
            <h2 id="transition-modal-title" className="modal-title">
              Save Prompt Template
            </h2>
            <Select
              sx={{ marginTop: "5px" }}
              variant="standard"
              fullWidth
              value={model}
              onChange={(e) => setModel(e.target.value)}
              displayEmpty
            >
              <MenuItem value="" disabled>
                Select model
              </MenuItem>
              {availableModels.map((model) => (
                <MenuItem key={model} value={model}>
                  {model}
                </MenuItem>
              ))}
            </Select>
            <TextField
              fullWidth
              required
              multiline
              variant="standard"
              label="Name"
              defaultValue={name}
              onChange={(e) => setName(e.target.value)}
            />

            <TextField
              fullWidth
              multiline
              required
              minRows={4}
              variant="outlined"
              label="Description"
              onChange={(e) => setDesc(e.target.value)}
            />

            <Grid container spacing={2} alignItems="center">
              <Grid item xs={6}>
                <Button
                  variant="contained"
                  color="success"
                  fullWidth
                  style={{ marginTop: "5px" }}
                  onClick={(e) => handleSavePrompt(e.target.value)}
                >
                  Save
                </Button>
              </Grid>
              <Grid item xs={6}>
                <Button
                  variant="contained"
                  color="error"
                  fullWidth
                  style={{ marginTop: "5px" }}
                  onClick={handleClose}
                >
                  Cancel
                </Button>
              </Grid>
            </Grid>
          </ModalContent>
        </Fade>
      </Modal>
    </div>
  );
};

const Backdrop = React.forwardRef((props, ref) => {
  const { open, ...other } = props;
  return (
    <Fade in={open}>
      <div ref={ref} {...other} />
    </Fade>
  );
});

Backdrop.propTypes = {
  open: PropTypes.bool,
};

const blue = {
  200: "#99CCFF",
  300: "#66B2FF",
  400: "#3399FF",
  500: "#007FFF",
  600: "#0072E5",
  700: "#0066CC",
};

const grey = {
  50: "#F3F6F9",
  100: "#E5EAF2",
  200: "#DAE2ED",
  300: "#C7D0DD",
  400: "#B0B8C4",
  500: "#9DA8B7",
  600: "#6B7A90",
  700: "#434D5B",
  800: "#303740",
  900: "#1C2025",
};

const Modal = styled(BaseModal)`
  position: fixed;
  z-index: 1300;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const StyledBackdrop = styled(Backdrop)`
  z-index: -1;
  position: fixed;
  inset: 0;
  background-color: rgb(0 0 0 / 0.5);
  -webkit-tap-highlight-color: transparent;
`;

const style = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  width: 400,
};

const ModalContent = styled("div")(
  ({ theme }) => css`
    font-family: "IBM Plex Sans", sans-serif;
    font-weight: 500;
    text-align: start;
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 8px;
    overflow: hidden;
    background-color: ${theme.palette.mode === "dark" ? grey[900] : "#fff"};
    border-radius: 8px;
    border: 1px solid ${theme.palette.mode === "dark" ? grey[700] : grey[200]};
    box-shadow: 0 4px 12px
      ${theme.palette.mode === "dark" ? "rgb(0 0 0 / 0.5)" : "rgb(0 0 0 / 0.2)"};
    padding: 24px;
    color: ${theme.palette.mode === "dark" ? grey[50] : grey[900]};

    & .modal-title {
      margin: 0;
      line-height: 1.5rem;
      margin-bottom: 8px;
    }

    & .modal-description {
      margin: 0;
      line-height: 1.5rem;
      font-weight: 400;
      color: ${theme.palette.mode === "dark" ? grey[400] : grey[800]};
      margin-bottom: 4px;
    }
  `,
);

export default TransitionsModal;
